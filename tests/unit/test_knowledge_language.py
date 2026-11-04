"""Pure Knowledge values and agreement with the Python provenance semantics."""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase, Source
from hypomnesis.epistemics.language import snapshot_value, support_value
from hypomnesis.epistemics.provenance import ONE, ZERO, Plus, Times, obs
from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.natives import default_registry
from hypomnesis.runtime.values import RecordValue
from hypomnesis.session import Session


@pytest.fixture(scope="module")
def context():
    holder = {"base": KnowledgeBase()}
    registry = default_registry()
    registry.register("test.knowledge", 1, lambda _: snapshot_value(holder["base"]))
    session = Session(registry)
    session.load('external input : unit -> Json.t Knowledge.t = "test.knowledge"')
    return holder, session


def test_program_derives_estimated_support_without_changing_original_base(context):
    holder, session = context
    base = KnowledgeBase()
    base.observe("width", 120, "plan")
    base.estimate("height", 80, "estimate", 0.6)
    holder["base"] = base
    original = base.journal
    session.load("""
let before = input ()
let after = Knowledge.derive before "area" (Json.Int 9600) "multiply" ["width"; "height"]
""")
    assert session.eval('Knowledge.support after "area"').value.tag == "Estimated"
    assert session.eval('Knowledge.known before "area"').value is False
    assert session.eval('Knowledge.value after "area"').value.tag == "Some"
    assert "area" not in base.facts and base.journal == original
    base.observe("width", 999, "new plan")
    assert session.eval('Knowledge.value before "width"').value.arg.arg == 120


def test_unknown_is_an_option_and_missing_premises_never_get_a_default(context):
    holder, session = context
    base = KnowledgeBase()
    base.unknown("width", "missing")
    holder["base"] = base
    assert session.eval('Knowledge.value (input ()) "width"').value.tag == "None"
    with pytest.raises(EvaluationError, match="unresolved property"):
        session.eval('Knowledge.derive (input ()) "x" Json.Null "bad" ["width"]')
    assert not base.facts


def test_constant_is_defaulted_and_repeated_premises_are_not_deduplicated(context):
    holder, session = context
    holder["base"] = KnowledgeBase()
    assert (
        session.eval("""
Knowledge.support (Knowledge.derive (input ()) "c" Json.Null "constant" []) "c"
""").value.tag
        == "Defaulted"
    )
    base = KnowledgeBase()
    base.estimate("x", 3, "a", 0.6)
    holder["base"] = base
    proof = session.eval("""
Knowledge.provenance (Knowledge.derive (input ()) "twice" Json.Null "joint" ["x"; "x"]) "twice"
""").value
    assert proof.tag == "Times" and proof.arg[0] == proof.arg[1]


def test_snapshot_requires_explicit_encoding_for_nominal_values():
    session = Session()
    session.load("module M = struct type box = { size : int } end")
    codec = TypeCodec(session.checker, "M.box")
    base = KnowledgeBase()
    base.observe("box", RecordValue("M.box", (("size", 3),)), "host")
    with pytest.raises(EvaluationError, match="not JSON data"):
        snapshot_value(base)
    snapshot = snapshot_value(base, encode=lambda fact: codec.encode(fact.value))
    assert snapshot.type_name == "Knowledge.t"


PROOFS = st.recursive(
    st.sampled_from([ZERO, ONE, obs("o"), obs("e"), obs("d"), obs("h")]),
    lambda children: st.one_of(
        st.builds(Plus, children, children), st.builds(Times, children, children)
    ),
    max_leaves=12,
)


@given(proof=PROOFS, retracted=st.sets(st.sampled_from(["o", "e", "d", "h"])))
def test_language_support_matches_python_for_alternatives_and_retractions(
    context, proof, retracted
):
    holder, session = context
    base = KnowledgeBase()
    for identifier, kind in [
        ("o", "observation"),
        ("e", "estimation"),
        ("d", "default"),
        ("h", "hypothesis"),
    ]:
        base.sources[identifier] = Source(identifier, kind, "host", 0.5)
    base.facts["x"] = Fact("x", 1, proof, "generated")
    base.retracted.update(retracted)
    holder["base"] = base
    result = session.eval("""
let base = input () in
Knowledge.grade base (Option.get (Knowledge.lookup base "x")).provenance
""").value
    assert result == support_value(base.support("x"))


def test_existence_is_not_confused_with_support_and_revision_still_removes_facts(context):
    holder, session = context
    base = KnowledgeBase()
    base.facts["unsupported"] = Fact("unsupported", 1, ZERO, "known but unsupported")
    holder["base"] = base
    assert session.eval('Knowledge.known (input ()) "unsupported"').value is True
    assert session.eval('Knowledge.support (input ()) "unsupported"').value.tag == "Unsupported"
    base.observe("observed", 2, "a")
    base.retract_source(base.source_id("observed"), "withdrawn")
    assert session.eval('Knowledge.value (input ()) "observed"').value.tag == "None"


def test_example_derives_the_surface_and_preserves_input():
    path = Path(__file__).resolve().parents[2] / "demo/examples/knowledge/plaque.hyp"
    session = Session()
    session.load(path.read_text(encoding="utf-8"))
    assert session.value("support").tag == "Estimated"
    assert session.value("surface").arg == 9600.0
    assert session.value("initial_inchange") is True
