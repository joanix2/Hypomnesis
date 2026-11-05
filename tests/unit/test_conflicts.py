"""Declared incompatibilities, complete evidence and non-destructive preferences."""

from dataclasses import FrozenInstanceError, replace

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.epistemics.conflicts import ConflictChecker, Invariant
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.metavariables import Proposal, ResolutionConflict, best_proposal
from hypomnesis.epistemics.provenance import ZERO, Support, obs
from hypomnesis.session import Session


def source_id(fact):
    return next(fact.provenance.observations())


def test_same_key_observations_are_not_lost_by_last_write_projection():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",)))
    first = base.observe("x", 1, "first observer")
    second = base.observe("x", 2, "second observer")
    before = (base.journal, dict(base.facts), dict(base.sources))
    scan = base.conflicts
    assert base.value("x") == 2 and scan.coherence == "conflict"
    (report,) = scan.conflicts
    assert report.facts == (first, second)
    assert {source.origin for source in report.sources} == {"first observer", "second observer"}
    assert report.selection is None and report.resolution == "report"
    assert not report.retracted_sources
    assert (base.journal, base.facts, base.sources) == before
    with pytest.raises(FrozenInstanceError):
        report.rule = "hidden"


@pytest.mark.parametrize(
    ("left", "right", "incompatible"),
    [
        (1, 1, False),
        (1, True, True),
        (1, 1.0, True),
        ([1], [True], True),
        ({"a": 1, "b": 2}, {"b": 2, "a": 1}, False),
        ([1], (1,), True),
    ],
)
def test_functional_equality_is_typed_snapshot_equality(left, right, incompatible):
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",)))
    base.observe("x", left, "one")
    base.observe("x", right, "two")
    assert bool(base.conflicts.conflicts) is incompatible


def test_support_preferences_never_erase_a_weaker_incompatible_assertion():
    checker = ConflictChecker(("x",), policy="best-support")
    base = KnowledgeBase(conflict_checker=checker)
    observed = base.observe("x", 3, "sensor")
    estimated = base.estimate("x", 8, "model", 0.99)
    (report,) = base.conflicts.conflicts
    assert report.selection == observed and report.resolution == "best-support"
    assert report.facts == (observed, estimated)
    assert base.value("x") == 8 and base.conflicts.coherence == "conflict"
    base.conflict_checker = replace(checker, policy="report")
    assert base.conflicts.conflicts[0].selection is None


def test_incompatible_best_support_has_no_order_or_confidence_tiebreaker():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",), policy="best-support"))
    base.estimate("x", 1, "one", 0.2)
    base.estimate("x", 2, "two", 0.9)
    (report,) = base.conflicts.conflicts
    assert report.selection is None and report.resolution == "tied-best-support"
    assert base.conflicts.coherence == "conflict"
    proposals = (
        Proposal(Fact("x", True, obs("a"), "test"), Support.OBSERVED),
        Proposal(Fact("x", 1, obs("b"), "test"), Support.OBSERVED),
    )
    with pytest.raises(ResolutionConflict):
        best_proposal(proposals, "x")


def test_explicit_revision_withdraws_old_assertion_without_erasing_history():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",)))
    first = base.observe("x", 1, "first")
    before = base.journal
    second = base.replace_observation("x", 2, "second", "correction")
    assert base.conflicts.coherence == "consistent"
    assert base.journal[: len(before)] == before
    assert source_id(first) in base.retracted and base.facts["x"] == second
    base.retract_source(source_id(second), "no longer available")
    assert base.conflicts.coherence == "unchecked"
    assert base.conflicts.pending[0].missing == ("x",)


def test_alternative_provenance_survives_and_its_support_is_recomputed():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",), policy="best-support"))
    observed = base.observe("input-a", 1, "sensor")
    estimated = base.estimate("input-b", 1, "model", 0.5)
    conclusion = Fact("x", 5, observed.provenance + estimated.provenance, "two proofs")
    base.publish_fact(conclusion)
    competing = base.observe("x", 6, "other sensor")
    assert base.conflicts.conflicts[0].resolution == "tied-best-support"
    base.retract_source(source_id(observed), "sensor withdrawn")
    (report,) = base.conflicts.conflicts
    assert report.selection == competing
    assert report.retracted_sources == (source_id(observed),)
    assert {source.id for source in report.sources} == {
        source_id(observed),
        source_id(estimated),
        source_id(competing),
    }
    base.retract_source(source_id(estimated), "model withdrawn")
    assert base.conflicts.coherence == "consistent"


def test_all_unsupported_assertions_are_unchecked_not_conflicting():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",)))
    base.publish_fact(Fact("x", 1, ZERO, "no evidence"))
    base.publish_fact(Fact("x", 2, ZERO, "no evidence"))
    assert not base.conflicts.conflicts and base.conflicts.coherence == "unchecked"


def test_default_and_observation_keep_distinct_support_and_coherence_axes():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",), policy="best-support"))
    base.derive("x", 1, "program constant", [])
    observed = base.observe("x", 2, "sensor")
    (report,) = base.conflicts.conflicts
    assert report.selection == observed and base.conflicts.coherence == "conflict"
    assert {source.kind for source in report.sources} == {"default", "observation"}


def test_unconfigured_keys_are_not_assumed_functional_or_consistent():
    base = KnowledgeBase()
    base.observe("x", 1, "one")
    base.observe("x", 2, "two")
    assert base.conflicts.coherence == "unchecked"
    base.conflict_checker = ConflictChecker(("unrelated",))
    assert base.conflicts.coherence == "unchecked" and not base.conflicts.conflicts


def test_invariant_uses_all_live_assertions_and_cites_the_exact_violating_tuple():
    invariant = Invariant(
        "ordered", ("low", "high"), lambda facts: facts[0].value <= facts[1].value
    )
    base = KnowledgeBase(
        conflict_checker=ConflictChecker(invariants=(invariant,), policy="best-support")
    )
    bad = base.observe("low", 9, "first lower bound")
    good = base.observe("low", 1, "second lower bound")
    assert base.conflicts.pending[0].missing == ("high",)
    high = base.observe("high", 5, "upper bound")
    (report,) = base.conflicts.conflicts
    assert report.kind == "invariant" and report.rule == "ordered"
    assert report.facts == (bad, high) and good not in report.facts
    assert {source.id for source in report.sources} == {source_id(bad), source_id(high)}
    assert report.selection is None and report.resolution == "invariant"
    base.retract_source(source_id(bad), "bad bound withdrawn")
    assert base.conflicts.coherence == "consistent"


def test_invariant_business_expression_can_run_in_the_symbolic_language():
    session = Session()
    session.load("let ordered (low : int) (high : int) = low <= high")

    def accepts(facts):
        return session.interpreter.apply(session.value("ordered"), [fact.value for fact in facts])

    base = KnowledgeBase(
        conflict_checker=ConflictChecker(invariants=(Invariant("order", ("a", "b"), accepts),))
    )
    base.observe("a", 9, "first")
    base.observe("b", 2, "second")
    assert base.conflicts.coherence == "conflict"
    base.replace_observation("a", 1, "corrected", "correction")
    assert base.conflicts.coherence == "consistent"


def test_predicate_errors_and_non_booleans_are_never_hidden():
    def broken(_):
        raise RuntimeError("predicate failed")

    base = KnowledgeBase()
    base.observe("x", 1, "sensor")
    with pytest.raises(RuntimeError, match="predicate failed"):
        ConflictChecker(invariants=(Invariant("broken", ("x",), broken),)).scan(base)
    with pytest.raises(ValueError, match="must return a bool"):
        ConflictChecker(invariants=(Invariant("bad", ("x",), lambda _: 1),)).scan(base)


def test_undeclared_provenance_is_rejected_not_treated_as_supported():
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",)))
    base.facts["x"] = Fact("x", 1, obs("undeclared"), "invalid host insertion")
    with pytest.raises(ValueError, match="undeclared"):
        _ = base.conflicts


@pytest.mark.parametrize(
    "make",
    [
        lambda: ConflictChecker(("x", "x")),
        lambda: ConflictChecker(policy="unknown"),
        lambda: Invariant("empty", (), lambda _: True),
        lambda: Invariant("bad", ("x", "x"), lambda _: True),
        lambda: Invariant("bad", ["x"], lambda _: True),
        lambda: ConflictChecker(invariants=[]),
        lambda: ConflictChecker(("x",), (Invariant("x", ("y",), lambda _: True),)),
    ],
)
def test_invalid_declarations_are_explicit_errors(make):
    with pytest.raises(ValueError):
        make()


@given(
    st.lists(st.integers(-3, 3), min_size=1, max_size=20),
    st.sets(st.integers(0, 19)),
)
def test_functional_reports_match_an_independent_live_assertion_oracle(values, withdrawn):
    base = KnowledgeBase(conflict_checker=ConflictChecker(("x",), policy="best-support"))
    claims = []
    for i, value in enumerate(values):
        fact = (
            base.observe("x", value, f"sensor-{i}")
            if i % 2 == 0
            else base.estimate("x", value, f"model-{i}", 0.5)
        )
        claims.append(fact)
    for i in sorted(withdrawn):
        if i < len(claims):
            base.retract_source(source_id(claims[i]), "withdrawn")
    active = [fact for i, fact in enumerate(claims) if i not in withdrawn]
    expected_conflict = len({fact.value for fact in active}) > 1
    before = base.journal
    scan = base.conflicts
    assert bool(scan.conflicts) == expected_conflict
    if expected_conflict:
        (report,) = scan.conflicts
        assert report.facts == tuple(active)
        assert {source.id for source in report.sources} == {source_id(fact) for fact in active}
        strongest = [fact for i, fact in enumerate(claims) if i not in withdrawn and i % 2 == 0]
        strongest = strongest or active
        if len({fact.value for fact in strongest}) == 1:
            assert report.selection is not None
            assert report.selection.value == strongest[0].value
        else:
            assert report.selection is None and report.resolution == "tied-best-support"
    else:
        assert scan.coherence == ("consistent" if active else "unchecked")
    assert base.journal == before


@given(
    st.lists(st.integers(-5, 5), min_size=1, max_size=8),
    st.lists(st.integers(-5, 5), min_size=1, max_size=8),
)
def test_invariant_reports_are_exactly_the_incompatible_pairs(left, right):
    checker = ConflictChecker(
        invariants=(
            Invariant("ordered", ("a", "b"), lambda facts: facts[0].value <= facts[1].value),
        )
    )
    base = KnowledgeBase(conflict_checker=checker)
    a = [base.observe("a", value, f"a-{i}") for i, value in enumerate(left)]
    b = [base.observe("b", value, f"b-{i}") for i, value in enumerate(right)]
    expected = {(source_id(x), source_id(y)) for x in a for y in b if x.value > y.value}
    actual = {
        tuple(source_id(fact) for fact in report.facts) for report in base.conflicts.conflicts
    }
    assert actual == expected
