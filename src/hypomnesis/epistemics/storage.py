"""Typed journal replay and transactional, append-only SQLite persistence."""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Mapping
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from hypomnesis.contracts.codec import CodecError, TypeCodec
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.epistemics.conflicts import ConflictChecker
from hypomnesis.epistemics.knowledge import AXIOM, Event, Fact, KnowledgeBase, Source, Unknown
from hypomnesis.epistemics.provenance import BOOLEAN, Obs, evaluate
from hypomnesis.epistemics.serialization import _type_document, from_json, to_json

SCHEMA_ID = "https://schemas.example.org/hypomnesis/knowledge-journal/1.0.0"
SQLITE_VERSION = 2
Codecs = Mapping[str, TypeCodec]


class JournalError(CodecError):
    """Malformed or divergent history, with a JSON path."""


class _Pairs(list[tuple[str, Any]]):
    pass


def _strict_json(encoded: str) -> Any:
    def convert(value: Any, path: str) -> Any:
        if isinstance(value, _Pairs):
            result = {}
            for key, child in value:
                location = f"{path}[{json.dumps(key)}]"
                if key in result:
                    raise JournalError(location, "duplicate JSON member")
                result[key] = convert(child, location)
            return result
        if isinstance(value, list):
            return [convert(child, f"{path}[{i}]") for i, child in enumerate(value)]
        if type(value) is float and not math.isfinite(value):
            raise JournalError(path, "non-finite JSON number")
        return value

    try:
        value = json.loads(encoded, object_pairs_hook=_Pairs)
    except json.JSONDecodeError as exc:
        raise JournalError("$", f"invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    return convert(value, "$")


def _json(data: Any) -> str:
    return json.dumps(
        data, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def _codec(codecs: Codecs, key: str, path: str) -> TypeCodec:
    codec = codecs.get(key)
    if not isinstance(codec, TypeCodec):
        raise JournalError(path + ".type", f"no trusted closed codec for {key!r}")
    return codec


def _at(path: str, error: CodecError) -> JournalError:
    message = str(error).removeprefix(error.path + ": ")
    return JournalError(path + error.path[1:], message)


def _checker_document(checker: ConflictChecker | None) -> dict[str, Any] | None:
    if checker is None:
        return None
    return {
        "functional": list(checker.functional),
        "policy": checker.policy,
        "invariants": [{"name": rule.name, "keys": list(rule.keys)} for rule in checker.invariants],
    }


def _checker(data: Any, supplied: ConflictChecker | None) -> ConflictChecker | None:
    if supplied is not None:
        if _checker_document(supplied) != data:
            raise JournalError("$.checker", "host checker does not match the stored declaration")
        return supplied
    if data is None:
        return None
    if data["invariants"]:
        raise JournalError("$.checker.invariants", "executable predicates require host bindings")
    try:
        return ConflictChecker(tuple(data["functional"]), policy=data["policy"])
    except ValueError as exc:
        raise JournalError("$.checker", str(exc)) from exc


def to_document(base: KnowledgeBase, codecs: Codecs) -> dict[str, Any]:
    registry = SchemaRegistry.with_builtin_schemas()

    def encode(value: Fact | Unknown | None, path: str) -> dict[str, Any] | None:
        if value is None:
            return None
        codec = _codec(codecs, value.key, path)
        try:
            return to_json(value, codec, registry=registry)
        except CodecError as exc:
            raise _at(path + ".value", exc) from exc

    events = [
        {
            "seq": event.seq,
            "kind": event.kind,
            "key": event.key,
            "detail": event.detail,
            "fact": encode(event.fact, f"$.events[{i}].fact"),
            "unknown": encode(event.unknown, f"$.events[{i}].unknown"),
        }
        for i, event in enumerate(base.journal)
    ]
    document = {
        "schema_version": "1.0.0",
        "sources": [asdict(source) for source in base.sources.values()],
        "events": events,
        "next_source_id": base._next_source_id,
        "checker": _checker_document(base.conflict_checker),
    }
    replayed = from_document(document, codecs, checker=base.conflict_checker)
    if (
        replayed.facts != base.facts
        or replayed.unknowns != base.unknowns
        or replayed.retracted != base.retracted
        or replayed.sources != base.sources
        or replayed.journal != base.journal
    ):
        raise JournalError("$.events", "state has changes not represented by the journal")
    return document


def from_document(
    document: Any,
    codecs: Codecs,
    *,
    checker: ConflictChecker | None = None,
) -> KnowledgeBase:
    registry = SchemaRegistry.with_builtin_schemas()
    registry.validate(SCHEMA_ID, document)
    if type(document["next_source_id"]) is not int:
        raise JournalError("$.next_source_id", "integer token expected")
    sources: dict[str, Source] = {}
    for i, data in enumerate(document["sources"]):
        source = Source(**data)
        if source.id in sources:
            raise JournalError(f"$.sources[{i}].id", "duplicate source")
        if source.id == AXIOM and source != Source(AXIOM, "default", "constante du programme"):
            raise JournalError(f"$.sources[{i}]", "incompatible program axiom source")
        sources[source.id] = source
    base = KnowledgeBase(sources=sources, conflict_checker=_checker(document["checker"], checker))
    direct_sources: set[str] = set()

    def decode(data: Any, path: str) -> Fact | Unknown | None:
        if data is None:
            return None
        codec = _codec(codecs, data["key"], path)
        try:
            value = from_json(data, codec, registry=registry)
        except CodecError as exc:
            prefix = path if data["type"] != _type_document(codec.type) else path + ".value"
            raise _at(prefix, exc) from exc
        if not isinstance(value, Fact | Unknown):
            raise JournalError(path, "event requires a fact or unknown")
        return value

    for i, data in enumerate(document["events"]):
        path = f"$.events[{i}]"
        if type(data["seq"]) is not int or data["seq"] != i + 1:
            raise JournalError(path + ".seq", "event sequence must be contiguous from 1")
        fact = decode(data["fact"], path + ".fact")
        unknown = decode(data["unknown"], path + ".unknown")
        if fact is not None and not isinstance(fact, Fact):
            raise JournalError(path + ".fact", "concrete fact expected")
        if unknown is not None and not isinstance(unknown, Unknown):
            raise JournalError(path + ".unknown", "unknown expected")
        event = Event(data["seq"], data["kind"], data["key"], data["detail"], fact, unknown)
        if any(value is not None and value.key != event.key for value in (fact, unknown)):
            raise JournalError(path + ".key", "event and snapshot keys differ")
        if fact is not None:
            missing = set(fact.provenance.observations()) - sources.keys()
            if missing:
                raise JournalError(
                    path + ".fact.provenance", f"undeclared sources: {sorted(missing)}"
                )
        kind = event.kind
        writes = kind in ("observed", "estimated", "hypothesis", "derived")
        needs_fact = writes or kind in ("replaced", "invalidated", "revised")
        needs_unknown = kind in ("unknown", "invalidated")
        if (fact is not None) != needs_fact or (unknown is not None) != needs_unknown:
            raise JournalError(path, "snapshots do not match the event kind")
        if writes and fact is not None:
            if kind != "derived":
                expected = {
                    "observed": "observation",
                    "estimated": "estimation",
                    "hypothesis": "hypothesis",
                }[kind]
                if (
                    not isinstance(fact.provenance, Obs)
                    or fact.premises
                    or sources[fact.provenance.id].kind != expected
                    or fact.provenance.id in base.retracted
                    or fact.provenance.id in direct_sources
                ):
                    raise JournalError(path + ".fact", "invalid direct source assertion")
                direct_sources.add(fact.provenance.id)
            if any(key not in base.facts for key in fact.premises):
                raise JournalError(path + ".fact.premises", "missing premise at this event")
            base.facts[event.key] = fact
            base.unknowns.pop(event.key, None)
        elif kind == "retracted":
            if event.key == AXIOM:
                raise JournalError(path + ".key", "program axiom cannot be retracted")
            base.retracted.add(event.key)
        elif kind in ("replaced", "revised", "invalidated"):
            if base.facts.get(event.key) != fact:
                raise JournalError(path + ".fact", "snapshot differs from the current fact")
            if kind == "invalidated" and fact is not None and unknown is not None:
                if not (set(fact.provenance.observations()) & base.retracted) or evaluate(
                    fact.provenance, BOOLEAN, lambda s: s not in base.retracted
                ):
                    raise JournalError(path + ".fact", "invalidation requires withdrawn evidence")
                del base.facts[event.key]
                base.unknowns[event.key] = unknown
        elif kind == "unknown" and unknown is not None:
            base.unknowns[event.key] = unknown
        base._journal.append(event)
    base._next_source_id = document["next_source_id"]
    return base


def export_json(base: KnowledgeBase, codecs: Codecs) -> str:
    return _json(to_document(base, codecs))


def import_json(
    encoded: str,
    codecs: Codecs,
    *,
    checker: ConflictChecker | None = None,
) -> KnowledgeBase:
    return from_document(_strict_json(encoded), codecs, checker=checker)


class SQLiteStore:
    def __init__(
        self,
        path: str | Path,
        codecs: Codecs,
        *,
        checker: ConflictChecker | None = None,
    ) -> None:
        self.codecs = dict(codecs)
        self.checker = checker
        self._connection = sqlite3.connect(path)
        try:
            self._migrate()
        except (sqlite3.Error, JournalError):
            self._connection.close()
            raise

    def __enter__(self) -> SQLiteStore:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._connection.close()

    def _migrate(self) -> None:
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            version = self._connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, SQLITE_VERSION):
                raise JournalError("$.sqlite.user_version", f"unsupported SQLite version {version}")
            if version == 0:
                tables = self._connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
                if tables:
                    raise JournalError("$.sqlite", "unversioned non-empty database")
                self._connection.execute(
                    "CREATE TABLE metadata "
                    "(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)"
                )
                self._connection.execute(
                    "CREATE TABLE events "
                    "(seq INTEGER PRIMARY KEY CHECK(seq>0), payload TEXT NOT NULL)"
                )
                self._connection.execute("PRAGMA user_version=1")
                version = 1
            if version == 1:
                for operation in ("UPDATE", "DELETE"):
                    self._connection.execute(
                        f"CREATE TRIGGER journal_no_{operation.lower()} "
                        f"BEFORE {operation} ON events "
                        "BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END"
                    )
                self._connection.execute("PRAGMA user_version=2")

    def _document(self) -> dict[str, Any]:
        row = self._connection.execute("SELECT payload FROM metadata WHERE id=1").fetchone()
        if row is None:
            raise JournalError("$.sqlite", "no journal saved")
        document = _strict_json(row[0])
        if not isinstance(document, dict) or "events" in document:
            raise JournalError("$.sqlite.metadata", "metadata object without events expected")
        events = []
        for i, (seq, payload) in enumerate(
            self._connection.execute("SELECT seq,payload FROM events ORDER BY seq")
        ):
            if seq != i + 1:
                raise JournalError(f"$.events[{i}].seq", "stored sequence has a gap")
            events.append(_strict_json(payload))
        document["events"] = events
        return document

    def load(self) -> KnowledgeBase:
        with self._connection:
            self._connection.execute("BEGIN")
            document = self._document()
            return from_document(document, self.codecs, checker=self.checker)

    def save(self, base: KnowledgeBase) -> None:
        document = to_document(base, self.codecs)
        if self.checker is not None and _checker_document(self.checker) != document["checker"]:
            raise JournalError("$.checker", "host checker does not match the saved declaration")
        if (
            self.checker is None
            and document["checker"] is not None
            and document["checker"]["invariants"]
        ):
            raise JournalError(
                "$.checker.invariants", "open the store with host invariant bindings"
            )
        events = document["events"]
        with self._connection:
            self._connection.execute("BEGIN IMMEDIATE")
            exists = self._connection.execute("SELECT 1 FROM metadata WHERE id=1").fetchone()
            previous = self._document() if exists else None
            offset = 0 if previous is None else len(previous["events"])
            if previous is not None:
                SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, previous)
                previous_checker = None
                if previous["checker"] is not None and previous["checker"]["invariants"]:
                    if self.checker is None:
                        raise JournalError("$.checker.invariants", "host bindings required")
                    previous_checker = replace(
                        self.checker,
                        functional=tuple(previous["checker"]["functional"]),
                        policy=previous["checker"]["policy"],
                    )
                from_document(previous, self.codecs, checker=previous_checker)
                if events[:offset] != previous["events"]:
                    raise JournalError(
                        "$.events", "history is not an extension of the stored prefix"
                    )
                if document["next_source_id"] < previous["next_source_id"]:
                    raise JournalError("$.next_source_id", "source counter cannot move backwards")
                current_sources = {source["id"]: source for source in document["sources"]}
                for source in previous["sources"]:
                    if current_sources.get(source["id"]) != source:
                        raise JournalError(
                            "$.sources", "previous sources cannot be changed or removed"
                        )
            self._connection.executemany(
                "INSERT INTO events(seq,payload) VALUES (?,?)",
                [(event["seq"], _json(event)) for event in events[offset:]],
            )
            metadata = {key: value for key, value in document.items() if key != "events"}
            self._connection.execute(
                "INSERT INTO metadata(id,payload) VALUES (1,?) "
                "ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                (_json(metadata),),
            )

    def export_json(self) -> str:
        return export_json(self.load(), self.codecs)

    def import_json(self, encoded: str) -> KnowledgeBase:
        base = import_json(encoded, self.codecs, checker=self.checker)
        self.save(base)
        return base

    def import_file(self, path: str | Path) -> KnowledgeBase:
        try:
            encoded = Path(path).read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise JournalError("$", f"invalid UTF-8 at byte {exc.start}") from exc
        return self.import_json(encoded)
