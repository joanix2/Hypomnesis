"""Versioned knowledge snapshots; the host supplies the expected closed type.

The knowledge schema checks metadata and provenance. TypeCodec separately
validates and reversibly encodes the concrete value, including nominal data.
Unknown has a type but no value. No untrusted source grades are deserialized:
support remains computed from declared sources and provenance.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from hypomnesis.contracts.codec import CodecError, TypeCodec, closed_type
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.epistemics.knowledge import Fact, Observation, Source, Unknown
from hypomnesis.epistemics.provenance import ONE, ZERO, Obs, One, Plus, Prov, Times, Zero
from hypomnesis.language.typesystem.types import TCon

SCHEMA_ID = "https://schemas.example.org/hypomnesis/knowledge/1.0.0"
Knowledge = Fact | Observation | Unknown


def _type_document(type_: TCon) -> dict[str, Any]:
    return {
        "name": type_.name,
        "args": [_type_document(closed_type(arg)) for arg in type_.args],
    }


def _encode_provenance(term: Prov) -> dict[str, Any]:
    if isinstance(term, Obs):
        return {"op": "obs", "id": term.id}
    if isinstance(term, Zero | One):
        return {"op": "zero" if isinstance(term, Zero) else "one"}
    if isinstance(term, Plus | Times):
        return {
            "op": "plus" if isinstance(term, Plus) else "times",
            "left": _encode_provenance(term.left),
            "right": _encode_provenance(term.right),
        }
    raise ValueError("invalid provenance term")


def _decode_provenance(data: dict[str, Any]) -> Prov:
    op = data["op"]
    if op == "obs":
        return Obs(data["id"])
    if op == "zero":
        return ZERO
    if op == "one":
        return ONE
    if op in ("plus", "times"):
        constructor = Plus if op == "plus" else Times
        return constructor(_decode_provenance(data["left"]), _decode_provenance(data["right"]))
    raise ValueError(f"invalid provenance operation: {op}")


def to_json(knowledge: Knowledge, codec: TypeCodec) -> dict[str, Any]:
    """Encode an immutable snapshot, checking concrete values against ``codec``."""
    data: dict[str, Any] = {"schema_version": "1.0.0"}
    if isinstance(knowledge, Observation):
        data.update(
            kind="observation", source=asdict(knowledge.source), fact=to_json(knowledge.fact, codec)
        )
    elif isinstance(knowledge, Fact):
        data.update(
            kind="fact",
            type=_type_document(codec.type),
            key=knowledge.key,
            value=codec.encode(knowledge.value),
            provenance=_encode_provenance(knowledge.provenance),
            method=knowledge.method,
            premises=list(knowledge.premises),
        )
    elif isinstance(knowledge, Unknown):
        data.update(
            kind="unknown",
            type=_type_document(codec.type),
            key=knowledge.key,
            description=knowledge.description,
        )
    else:
        raise ValueError("expected Fact, Observation or Unknown")
    SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, data)
    return data


def from_json(data: Any, codec: TypeCodec) -> Knowledge:
    """Validate metadata and the host's expected type, then reconstruct a snapshot.

    The standalone schema deliberately does not validate ``value`` against a
    language type: only this function, with a trusted TypeCodec, does so.
    No knowledge base is mutated and no rule or plugin is executed.
    """
    SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, data)
    if data["kind"] == "observation":
        fact = from_json(data["fact"], codec)
        if not isinstance(fact, Fact):
            raise ValueError("observation requires a concrete fact")
        return Observation(Source(**data["source"]), fact)
    if data["type"] != _type_document(codec.type):
        raise CodecError("$.type", "knowledge type does not match the expected closed type")
    if data["kind"] == "unknown":
        return Unknown(data["key"], data["description"])
    return Fact(
        data["key"],
        codec.decode(data["value"]),
        _decode_provenance(data["provenance"]),
        data["method"],
        tuple(data["premises"]),
    )
