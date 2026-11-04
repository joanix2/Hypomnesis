"""Typed holes, competing evidence and explicit resolution (HYP-032)."""

from dataclasses import FrozenInstanceError, replace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.contracts.codec import CodecError, TypeCodec
from hypomnesis.epistemics.knowledge import Fact, Unknown
from hypomnesis.epistemics.metavariables import (
    Constraint,
    MetaVar,
    ResolutionConflict,
    UnresolvedMetaVar,
    best,
    conflict,
    propose,
    resolve,
)
from hypomnesis.epistemics.provenance import Support, obs
from hypomnesis.runtime.values import RecordValue
from hypomnesis.session import Session


@pytest.fixture(scope="module")
def codec():
    return TypeCodec(Session().checker, "int")


def test_unknown_never_has_a_concrete_value_or_an_invented_support(codec):
    meta = MetaVar("object.size", codec)
    assert meta.type.name == "int" and meta.state == "unresolved"
    assert meta.grade is None and meta.selected is None
    assert meta.coherence == "consistent"
    with pytest.raises(UnresolvedMetaVar):
        _ = meta.value
    with pytest.raises(UnresolvedMetaVar):
        best(meta)
    with pytest.raises(UnresolvedMetaVar):
        resolve(meta)
    with pytest.raises(ValueError):
        Fact("value", meta, obs("s"), "cannot use a hole as data")
    with pytest.raises(FrozenInstanceError):
        meta.id = "changed"


def test_two_sources_select_the_best_support_without_mutating_the_hole(codec):
    meta = MetaVar("object.size", codec)
    estimated = propose(meta, 3, Support.ESTIMATED, obs("estimator"))
    observed = propose(estimated, 3, Support.OBSERVED, obs("sensor"))
    assert len(meta.proposals) == 0 and len(estimated.proposals) == 1
    assert observed.state == "proposed" and observed.grade is None
    assert best(observed).fact.provenance == obs("sensor")
    chosen = resolve(observed)
    assert chosen.state == "resolved" and chosen.value == 3
    assert chosen.grade == Support.OBSERVED and not conflict(chosen)
    assert len(chosen.proposals) == 2
    assert observed.state == "proposed"


def test_a_stronger_proposal_never_hides_an_incompatible_weaker_one(codec):
    meta = propose(MetaVar("x", codec), 2, Support.ESTIMATED, obs("estimator"))
    meta = propose(meta, 3, Support.OBSERVED, obs("sensor"))
    assert best(meta).grade == Support.OBSERVED
    assert conflict(meta) and meta.coherence == "conflict"
    with pytest.raises(ResolutionConflict, match="explicit choice"):
        resolve(meta)
    selected = resolve(meta, choice=1)
    assert selected.value == 3 and selected.grade == Support.OBSERVED
    assert conflict(selected) and selected.coherence == "conflict"
    assert len(selected.proposals) == 2


def test_equal_support_disagreement_has_no_insertion_order_winner(codec):
    meta = propose(MetaVar("x", codec), 2, Support.OBSERVED, obs("a"))
    meta = propose(meta, 3, Support.OBSERVED, obs("b"))
    with pytest.raises(ResolutionConflict, match="best-supported"):
        best(meta)
    assert resolve(meta, choice=0).value == 2
    assert resolve(meta, choice=1).value == 3


def test_new_evidence_reopens_resolution_without_erasing_previous_state(codec):
    first = resolve(propose(MetaVar("x", codec), 2, Support.ESTIMATED, obs("a")))
    second = propose(first, 3, Support.OBSERVED, obs("b"))
    assert first.value == 2 and first.state == "resolved"
    assert second.state == "proposed" and second.grade is None
    with pytest.raises(UnresolvedMetaVar):
        _ = second.value
    assert conflict(second)


@pytest.mark.parametrize("value", [True, 1.0, "1", None, Unknown("x", "missing")])
def test_type_mismatches_are_rejected_without_changing_proposals(codec, value):
    meta = MetaVar("x", codec)
    with pytest.raises((CodecError, ValueError)):
        propose(meta, value, Support.ESTIMATED, obs("a"))
    assert not meta.proposals


def test_constraints_are_named_and_checked_before_accepting_a_proposal(codec):
    meta = MetaVar("x", codec, (Constraint("positive", lambda n: n > 0),))
    with pytest.raises(ValueError, match="positive"):
        propose(meta, -1, Support.ESTIMATED, obs("a"))
    assert not meta.proposals
    assert resolve(propose(meta, 2, Support.ESTIMATED, obs("a"))).value == 2


def test_truthy_constraint_results_are_not_boolean_approval(codec):
    meta = MetaVar("x", codec, (Constraint("boolean", lambda _: "yes"),))
    with pytest.raises(ValueError, match="boolean"):
        propose(meta, 2, Support.ESTIMATED, obs("a"))


def test_constraint_errors_are_explicit_and_leave_original_state_intact(codec):
    def broken(_):
        raise RuntimeError("constraint unavailable")

    meta = MetaVar("x", codec, (Constraint("broken", broken),))
    with pytest.raises(RuntimeError, match="constraint unavailable"):
        propose(meta, 2, Support.ESTIMATED, obs("a"))
    assert meta.state == "unresolved" and not meta.proposals


@pytest.mark.parametrize("grade", [Support.UNSUPPORTED, "Observed", 0])
def test_missing_or_untyped_evidence_is_rejected(codec, grade):
    with pytest.raises(ValueError):
        propose(MetaVar("x", codec), 2, grade, obs("a"))


@pytest.mark.parametrize("choice", [-1, 1, True, "0"])
def test_explicit_choice_must_select_an_existing_proposal(codec, choice):
    meta = propose(MetaVar("x", codec), 2, Support.HYPOTHESIS, obs("a"))
    with pytest.raises(ValueError, match="existing proposal"):
        resolve(meta, choice=choice)


def test_constructor_cannot_inject_a_wrong_type_or_property(codec):
    original = propose(MetaVar("x", codec), 2, Support.OBSERVED, obs("a"))
    with pytest.raises(ValueError, match="different metavariable"):
        replace(original, id="other")
    with pytest.raises(CodecError):
        replace(original, codec=TypeCodec(Session().checker, "string"))
    with pytest.raises(ValueError, match="immutable"):
        MetaVar("x", codec, constraints=[])


def test_nominal_values_are_preserved_by_the_existing_closed_type_codec():
    session = Session()
    session.load("module M = struct type box = { size : int } end")
    meta = MetaVar("object.box", TypeCodec(session.checker, "M.box"))
    value = RecordValue("M.box", (("size", 3),))
    selected = resolve(propose(meta, value, Support.ESTIMATED, obs("a")))
    assert selected.value == value
    assert selected.value is not value
    assert selected.selected.fact.provenance == obs("a")


@given(
    value=st.integers(),
    grades=st.lists(st.sampled_from(list(Support)[:-1]), min_size=1, max_size=8),
)
def test_best_agreeing_evidence_is_exactly_the_minimum_support(value, grades):
    meta = MetaVar("x", TypeCodec(Session().checker, "int"))
    for index, grade in enumerate(grades):
        meta = propose(meta, value, grade, obs(f"source-{index}"))
    assert best(meta).grade == min(grades)
    assert resolve(meta).value == value
    assert resolve(meta).grade == min(grades)
    assert not conflict(meta)
