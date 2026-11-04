"""Forward chaining, exact budgets, alternatives and defeasible defaults."""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.engine.rules import Conclusion, Rule, RuleConflict, RuleEngine, language_rule
from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase, Source
from hypomnesis.epistemics.provenance import Support, obs
from hypomnesis.session import Session


def increment(name, target, premise):
    return Rule(name, target, (premise,), lambda values: Conclusion(values[0] + 1))


def test_observation_and_estimation_produce_estimated_conclusion():
    base = KnowledgeBase()
    base.observe("width", 120, "plan")
    base.estimate("height", 80, "estimate", 0.6)
    rule = Rule(
        "area", "area", ("width", "height"), lambda values: Conclusion(values[0] * values[1])
    )
    engine = RuleEngine(base, (rule,))
    report = engine.run()
    assert report.status == "fixed_point" and report.evaluations == 2 and report.published == 1
    assert base.value("area") == 9600 and base.support("area") == Support.ESTIMATED
    assert base.confidence("area") == 0.6
    journal = base.journal
    assert engine.run().published == 0 and base.journal == journal


@given(length=st.integers(1, 10))
def test_reversed_chain_reaches_its_least_fixed_point_with_exact_bound(length):
    base = KnowledgeBase()
    base.estimate("x0", 0, "input", 0.8)
    rules = tuple(increment(f"r{i}", f"x{i}", f"x{i - 1}") for i in reversed(range(1, length + 1)))
    report = RuleEngine(base, rules).run(budget=length * (length + 1))
    assert report.status == "fixed_point" and report.published == length
    assert report.evaluations == length * (length + 1)
    assert base.value(f"x{length}") == length
    assert base.support(f"x{length}") == Support.ESTIMATED


def test_exact_budget_distinguishes_unverified_point_from_fixed_point():
    base = KnowledgeBase()
    calls = []
    rule = Rule("constant", "x", (), lambda _: calls.append(1) or Conclusion(2))
    engine = RuleEngine(base, (rule,))
    report = engine.run(budget=0)
    assert report.status == "budget_exhausted" and report.evaluations == 0 and not calls
    report = engine.run(budget=1)
    assert report.status == "budget_exhausted" and report.evaluations == len(calls) == 1
    assert base.value("x") == 2 and base.support("x") == Support.DEFAULTED
    report = engine.run(budget=1)
    assert report.status == "fixed_point" and report.evaluations == 1 and report.published == 0
    assert len(calls) == 2
    assert RuleEngine(KnowledgeBase(), ()).run(budget=0).status == "fixed_point"


def test_alternative_justifications_survive_retraction_and_rerun_is_idempotent():
    base = KnowledgeBase()
    base.observe("a", 1, "sensor")
    base.estimate("b", 1, "estimate", 0.5)
    rules = (
        Rule("from-a", "x", ("a",), lambda values: Conclusion(values[0])),
        Rule("from-b", "x", ("b",), lambda values: Conclusion(values[0])),
    )
    engine = RuleEngine(base, rules)
    assert engine.run().status == "fixed_point"
    assert base.support("x") == Support.OBSERVED
    journal = base.journal
    assert engine.run().published == 0 and base.journal == journal
    base.retract_source(base.source_id("a"), "withdraw a")
    assert base.value("x") == 1 and base.support("x") == Support.ESTIMATED
    assert engine.run().status == "fixed_point"
    assert base.support("x") == Support.ESTIMATED


def test_revision_invalidates_and_rederives_the_chain():
    base = KnowledgeBase()
    base.observe("x", 1, "sensor")
    engine = RuleEngine(base, (increment("y", "y", "x"), increment("z", "z", "y")))
    engine.run()
    base.replace_observation("x", 10, "sensor", "new measurement")
    assert "y" not in base.facts and "z" not in base.facts
    assert engine.run().status == "fixed_point"
    assert base.value("y") == 11 and base.value("z") == 12


def test_observation_defeats_default_and_invalidates_its_dependents():
    base = KnowledgeBase()
    default = Rule("fallback", "x", (), lambda _: Conclusion(2), default=True)
    engine = RuleEngine(base, (default, increment("y", "y", "x")))
    engine.run()
    old_sources = set(base.facts["x"].provenance.observations())
    assert base.support("x") == base.support("y") == Support.DEFAULTED
    base.observe("x", 7, "sensor")
    report = engine.run()
    assert report.status == "fixed_point"
    assert (old_sources - {"axiome"}) <= base.retracted
    assert base.value("x") == 7 and base.value("y") == 8
    assert base.support("y") == Support.OBSERVED
    assert any(e.kind == "invalidated" and e.key == "y" for e in base.journal)


def test_default_is_not_promoted_by_its_observed_premises():
    base = KnowledgeBase()
    base.observe("x", 1, "sensor")
    rule = Rule("default", "y", ("x",), lambda values: Conclusion(values[0]), default=True)
    RuleEngine(base, (rule,)).run()
    assert base.support("y") == Support.DEFAULTED


def test_repeated_premises_preserve_confidence_multiplication():
    base = KnowledgeBase()
    base.estimate("x", 1, "a", 0.5)
    rule = Rule("twice", "y", ("x", "x"), lambda _: Conclusion(2))
    RuleEngine(base, (rule,)).run()
    assert base.facts["y"].premises == ("x", "x")
    assert base.confidence("y") == 0.25


@pytest.mark.parametrize(("left", "right"), [(1, 2), (1, True), ({"x": [1]}, {"x": [True]})])
def test_incompatible_values_and_distinct_scalar_types_are_reported(left, right):
    base = KnowledgeBase()
    rules = (
        Rule("first", "x", (), lambda _: Conclusion(left)),
        Rule("second", "x", (), lambda _: Conclusion(right)),
    )
    with pytest.raises(RuleConflict) as caught:
        RuleEngine(base, rules).run()
    assert caught.value.target == "x"
    assert len(caught.value.facts) == 2


def test_conditions_and_missing_premises_are_not_failures_or_fabricated_values():
    base = KnowledgeBase()
    rules = (
        increment("missing", "x", "missing"),
        Rule("false-condition", "y", (), lambda _: None),
        Rule("null-value", "z", (), lambda _: Conclusion(None)),
    )
    report = RuleEngine(base, rules).run()
    assert report.status == "fixed_point"
    assert "x" not in base.facts and "y" not in base.facts and base.value("z") is None


def test_recursive_provenance_growth_stops_at_budget_not_false_fixed_point():
    base = KnowledgeBase()
    rules = (
        Rule("seed", "a", (), lambda _: Conclusion(1)),
        Rule("forward", "b", ("a",), lambda values: Conclusion(values[0])),
        Rule("backward", "a", ("b",), lambda values: Conclusion(values[0])),
    )
    report = RuleEngine(base, rules).run(budget=12)
    assert report.status == "budget_exhausted" and report.evaluations == 12


def test_invalid_callback_and_missing_sources_are_explicit_without_partial_publication():
    base = KnowledgeBase()
    with pytest.raises(ValueError, match="Conclusion or None"):
        RuleEngine(base, (Rule("bad", "x", (), lambda _: 1),)).run()
    assert not base.facts and not base.sources and not base.journal
    fact = Fact("x", 1, obs("missing"), "bad")
    source = Source("other", "default", "unused")
    with pytest.raises(ValueError, match="undeclared"):
        base.publish_fact(fact, sources=(source,))
    assert not base.facts and not base.sources and not base.journal


def test_business_logic_can_be_a_typed_hypomnesis_function():
    session = Session()
    root = Path(__file__).resolve().parents[2]
    session.load((root / "demo/examples/knowledge/regles.hyp").read_text())
    rule = language_rule(session, "area", "area", ("width", "height"), "surface")
    base = KnowledgeBase()
    base.observe("width", 120, "plan")
    base.estimate("height", 80, "estimate", 0.6)
    assert RuleEngine(base, (rule,)).run().status == "fixed_point"
    assert base.value("area") == 9600 and base.support("area") == Support.ESTIMATED
    absent = KnowledgeBase()
    absent.observe("width", -1, "plan")
    absent.observe("height", 2, "plan")
    assert RuleEngine(absent, (rule,)).run().published == 0
    assert "area" not in absent.facts
    session.load("let null_rule (_ : Json.t list) = Some Json.Null")
    null_rule = language_rule(session, "null", "null", (), "null_rule")
    assert RuleEngine(absent, (null_rule,)).run().status == "fixed_point"
    assert absent.value("null") is None
    with pytest.raises(ValueError, match=r"Json\.t list"):
        language_rule(session, "bad", "x", (), "Int.abs")


@pytest.mark.parametrize("budget", [-1, True, 1.5])
def test_invalid_budgets_are_rejected(budget):
    with pytest.raises(ValueError, match="budget"):
        RuleEngine(KnowledgeBase(), ()).run(budget=budget)


def test_overriding_downstream_conclusion_does_not_revoke_ancestral_default():
    base = KnowledgeBase()
    rules = (
        Rule("fallback", "x", (), lambda _: Conclusion(2), default=True),
        increment("y", "y", "x"),
        increment("z", "z", "x"),
    )
    engine = RuleEngine(base, rules)
    engine.run()
    base.observe("y", 3, "sensor")
    engine.run()
    assert not base.retracted
    assert base.value("x") == 2 and base.value("z") == 3
    assert base.support("y") == Support.OBSERVED
    assert base.support("x") == base.support("z") == Support.DEFAULTED


def test_alternative_object_key_orders_do_not_conflict_or_oscillate():
    base = KnowledgeBase()
    rules = (
        Rule("first", "x", (), lambda _: Conclusion({"a": 1, "b": [2]})),
        Rule("second", "x", (), lambda _: Conclusion({"b": [2], "a": 1})),
    )
    engine = RuleEngine(base, rules)
    assert engine.run(budget=10).status == "fixed_point"
    journal = base.journal
    assert engine.run().published == 0 and base.journal == journal


def test_publication_rejects_stronger_axiom_and_missing_premises_atomically():
    base = KnowledgeBase()
    with pytest.raises(ValueError, match="axiom"):
        base.publish_fact(
            Fact("x", 1, obs("axiome"), "rule"),
            sources=(Source("axiome", "observation", "forged"),),
        )
    with pytest.raises(ValueError, match="missing premises"):
        base.publish_fact(Fact("x", 1, obs("axiome"), "rule", ("absent",)))
    assert not base.facts and not base.sources and not base.journal


def test_callback_failure_is_propagated_without_fabricating_a_conclusion():
    def fail(_):
        raise RuntimeError("rule failed")

    base = KnowledgeBase()
    with pytest.raises(RuntimeError, match="rule failed"):
        RuleEngine(base, (Rule("failure", "x", (), fail),)).run()
    assert not base.facts and not base.journal
