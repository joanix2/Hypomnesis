"""Immutable knowledge snapshots and their typed JSON boundary (HYP-030)."""

import json
from dataclasses import FrozenInstanceError

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.contracts.codec import CodecError, TypeCodec
from hypomnesis.contracts.registry import ContractError, SchemaRegistry
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase, Observation, Source, Unknown
from hypomnesis.epistemics.provenance import ONE, ZERO, Support, obs
from hypomnesis.epistemics.serialization import SCHEMA_ID, from_json, to_json
from hypomnesis.runtime.values import RecordValue, Variant, from_iterable
from hypomnesis.session import Session


@pytest.fixture(scope="module")
def session():
    s = Session()
    s.load("module Model = struct type box = { size : int; ok : bool } end")
    return s


def wire(value, codec):
    encoded = json.loads(json.dumps(to_json(value, codec), allow_nan=False))
    SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, encoded)
    return encoded


def test_facts_snapshot_inputs_and_return_detached_values():
    value = {"items": [1, {"ok": True}]}
    fact = Fact("object.data", value, obs("sensor-1"), "observed")
    value["items"].append(42)
    fact.value["items"][1]["ok"] = False
    assert fact.value == {"items": [1, {"ok": True}]}
    with pytest.raises(FrozenInstanceError):
        fact.key = "other"
    with pytest.raises(FrozenInstanceError):
        fact.provenance.id = "other"


def test_nominal_values_are_snapshotted_recursively():
    payload = {"items": [2]}
    record = RecordValue("Model.box", (("payload", Variant("Data", payload, 1)),))
    fact = Fact("object.box", record, obs("sensor-1"), "observed")
    payload["items"].clear()
    fact.value.get("payload").arg["items"].append(3)
    assert fact.value.get("payload").arg == {"items": [2]}


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), {1: "bad"}, object(), Unknown("x", "missing")]
)
def test_non_data_and_non_finite_values_are_rejected(value):
    with pytest.raises(ValueError):
        Fact("x", value, obs("s"), "test")


def test_cycles_are_rejected_but_shared_subvalues_are_allowed():
    data = []
    data.append(data)
    with pytest.raises(ValueError, match="cyclic"):
        Fact("x", data, obs("s"), "test")
    shared = [1]
    assert Fact("x", (shared, shared), obs("s"), "test").value == ([1], [1])


@pytest.mark.parametrize(
    "build",
    [
        lambda: Fact("", 1, obs("s"), "test"),
        lambda: Fact("x", 1, obs(""), "test"),
        lambda: Fact("x", 1, obs("s"), ""),
        lambda: Fact("x", 1, obs("s"), "test", ["a"]),
        lambda: Fact("x", 1, obs("s"), "test", ("",)),
        lambda: Fact("x", 1, "observed", "test"),
        lambda: Source("s", "derived", "rule"),
        lambda: Source("", "observation", "sensor"),
        lambda: Source("s", "observation", ""),
        lambda: Source("s", "estimation", "model", True),
        lambda: Source("s", "estimation", "model", float("nan")),
        lambda: Source("s", "estimation", "model", 1.1),
        lambda: Unknown("x", ""),
    ],
)
def test_invalid_metadata_is_rejected(build):
    with pytest.raises(ValueError):
        build()


def test_failed_record_does_not_change_facts_sources_or_journal():
    kb = KnowledgeBase()
    kb.observe("a", 1, "sensor")
    before = (dict(kb.sources), dict(kb.facts), list(kb.journal))
    with pytest.raises(ValueError):
        kb.observe("b", object(), "sensor")
    assert before == (kb.sources, kb.facts, kb.journal)
    with pytest.raises(ValueError):
        kb.derive("b", object(), "constant", [])
    assert before == (kb.sources, kb.facts, kb.journal)


def test_support_remains_provenance_driven_and_unknown_is_not_a_value():
    kb = KnowledgeBase()
    kb.unknown("x", "missing value")
    kb.observe("a", 1, "sensor")
    kb.estimate("b", 2, "model", 0.8)
    derived = kb.derive("x", 3, "sum", ["a", "b"])
    assert derived.premises == ("a", "b")
    assert kb.support("x") == Support.ESTIMATED
    assert "x" not in kb.unknowns
    assert kb.sources[kb.source_id("a")].support == Support.OBSERVED
    assert Source("d", "default", "fallback").support == Support.DEFAULTED
    assert Source("h", "hypothesis", "assumption").support == Support.HYPOTHESIS
    with pytest.raises(KeyError):
        kb.value("unresolved")


@pytest.mark.parametrize(
    "signature,value",
    [
        ("int", 10**80),
        ("float", 0.125),
        ("bool", True),
        ("string", "observé"),
        ("unit", ()),
        ("int list", from_iterable([1, 2])),
        ("int * string", (1, "x")),
        ("int option", Variant("Some", 1, 1)),
        ("Model.box", RecordValue("Model.box", (("size", 3), ("ok", True)))),
    ],
)
def test_typed_fact_roundtrip(session, signature, value):
    codec = TypeCodec(session.checker, signature)
    fact = Fact("object.value", value, (obs("sensor-1") + ZERO) * ONE, "rule", ("input",))
    assert from_json(wire(fact, codec), codec) == fact


def test_observation_identity_and_source_roundtrip(session):
    codec = TypeCodec(session.checker, "int")
    fact = Fact("object.size", 3, obs("sensor-42"), "measurement")
    observation = Observation(Source("sensor-42", "observation", "sensor"), fact)
    restored = from_json(wire(observation, codec), codec)
    assert restored == observation
    assert isinstance(restored, Observation) and restored.id == "sensor-42"
    with pytest.raises(FrozenInstanceError):
        observation.source.origin = "changed"
    for source in [
        Source("other", "observation", "sensor"),
        Source("sensor-42", "estimation", "model"),
    ]:
        with pytest.raises(ValueError):
            Observation(source, fact)
    with pytest.raises(ValueError):
        Observation(
            observation.source,
            Fact(fact.key, fact.value, fact.provenance, fact.method, ("a",)),
        )


def test_unknown_roundtrip_has_type_but_no_concrete_value(session):
    codec = TypeCodec(session.checker, "int")
    unknown = Unknown("object.size", "size to solve")
    encoded = wire(unknown, codec)
    assert encoded["kind"] == "unknown"
    assert "value" not in encoded and "provenance" not in encoded
    assert from_json(encoded, codec) == unknown
    with pytest.raises(ValueError):
        Fact("x", unknown, obs("s"), "test")


@pytest.mark.parametrize(
    "patch",
    [
        {"schema_version": "2.0.0"},
        {"grade": "Observed"},
        {"key": " "},
        {"provenance": {"op": "mystery"}},
        {"provenance": {"op": "obs", "id": "s", "extra": True}},
        {"premises": [""]},
    ],
)
def test_closed_schema_rejects_bad_metadata(session, patch):
    codec = TypeCodec(session.checker, "int")
    encoded = to_json(Fact("x", 1, obs("s"), "test"), codec)
    encoded.update(patch)
    with pytest.raises(ContractError):
        from_json(encoded, codec)


def test_type_and_value_are_checked_in_both_directions(session):
    integer = TypeCodec(session.checker, "int")
    boolean = TypeCodec(session.checker, "bool")
    fact = Fact("x", 1, obs("s"), "test")
    with pytest.raises(CodecError):
        to_json(fact, boolean)
    encoded = to_json(fact, integer)
    with pytest.raises(CodecError, match="expected closed type"):
        from_json(encoded, boolean)
    encoded["value"] = True
    with pytest.raises(CodecError):
        from_json(encoded, integer)
    encoded["value"] = float("nan")
    with pytest.raises(CodecError):
        from_json(encoded, integer)


def test_snapshot_equality_preserves_scalar_types():
    assert Fact("x", 1, obs("s"), "test") != Fact("x", True, obs("s"), "test")
    assert Fact("x", 1, obs("s"), "test") != Fact("x", 1.0, obs("s"), "test")


def test_repeated_premises_keep_existing_semiring_meaning(session):
    kb = KnowledgeBase()
    kb.estimate("x", 2, "model", 0.5)
    fact = kb.derive("square", 4, "product", ["x", "x"])
    assert kb.confidence("square") == 0.25
    codec = TypeCodec(session.checker, "int")
    assert from_json(wire(fact, codec), codec) == fact


def test_observation_json_must_reference_its_own_source(session):
    codec = TypeCodec(session.checker, "int")
    fact = Fact("x", 1, obs("s"), "measurement")
    encoded = to_json(Observation(Source("s", "observation", "sensor"), fact), codec)
    encoded["source"]["id"] = "other"
    with pytest.raises(ValueError, match="directly reference"):
        from_json(encoded, codec)


@given(st.integers(), st.text(min_size=1).filter(lambda s: bool(s.strip())))
def test_generated_fact_id_and_value_survive_json(session, value, identifier):
    codec = TypeCodec(session.checker, "int")
    fact = Fact(identifier, value, obs(identifier), "generated")
    assert from_json(wire(fact, codec), codec) == fact
