"""Python instances of the provenance theorems in Epistemics/Provenance.lean."""

from fractions import Fraction

from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.epistemics.provenance import (
    BOOLEAN,
    CONFIDENCE,
    COST,
    ONE,
    SUPPORT,
    ZERO,
    Semiring,
    Support,
    evaluate,
    obs,
    retract,
    substitute,
)

IDS = ("a", "b", "c")
TERMS = st.recursive(
    st.one_of(st.sampled_from(IDS).map(obs), st.sampled_from((ZERO, ONE))),
    lambda children: st.one_of(
        st.tuples(children, children).map(lambda p: p[0] + p[1]),
        st.tuples(children, children).map(lambda p: p[0] * p[1]),
    ),
    max_leaves=15,
)
VALUATIONS = st.fixed_dictionaries({i: st.integers(min_value=0, max_value=10) for i in IDS})


@given(TERMS, st.tuples(TERMS, TERMS, TERMS), VALUATIONS)
def test_eval_subst(term, replacements, values):
    """Prov.eval_subst: evaluation commutes with arbitrary substitution."""
    sigma = dict(zip(IDS, replacements, strict=True))
    for semiring, valuation in [
        (BOOLEAN, lambda i: bool(values[i] % 2)),
        (SUPPORT, lambda i: Support(values[i] % 5)),
        (COST, lambda i: float(values[i])),
    ]:
        assert evaluate(substitute(term, sigma.__getitem__), semiring, valuation) == evaluate(
            term, semiring, lambda i, s=semiring, v=valuation: evaluate(sigma[i], s, v)
        )


@given(TERMS, st.sampled_from(IDS), st.dictionaries(st.sampled_from(IDS), st.booleans()))
def test_holds_after_retract(term, removed, values):
    """holds_after_retract: x := zero agrees with marking x false."""
    value = lambda i: values.get(i, False)
    assert evaluate(substitute(term, retract(removed)), BOOLEAN, value) == evaluate(
        term, BOOLEAN, lambda i: i != removed and value(i)
    )


@given(TERMS, VALUATIONS)
def test_retract_unrelated(term, values):
    """retract_unrelated: absent observations cannot change any reading."""
    assert "unrelated" not in set(term.observations())
    for semiring, valuation in [
        (BOOLEAN, lambda i: bool(values[i] % 2)),
        (SUPPORT, lambda i: Support(values[i] % 5)),
        (COST, lambda i: float(values[i])),
        (CONFIDENCE, lambda i: values[i] / 10),
    ]:
        assert evaluate(substitute(term, retract("unrelated")), semiring, valuation) == evaluate(
            term, semiring, valuation
        )


@given(TERMS, VALUATIONS, VALUATIONS)
def test_support_mono(term, first, second):
    """support_mono: weakening every source cannot improve a conclusion."""
    better = {i: Support(min(first[i] % 5, second[i] % 5)) for i in IDS}
    worse = {i: Support(max(first[i] % 5, second[i] % 5)) for i in IDS}
    assert evaluate(term, SUPPORT, better.__getitem__) <= evaluate(term, SUPPORT, worse.__getitem__)


@given(TERMS, TERMS, VALUATIONS)
def test_conjunction_no_stronger(first, second, values):
    """conjunction_no_stronger: joint premises cannot improve support."""
    grade = lambda i: Support(values[i] % 5)
    assert evaluate(first, SUPPORT, grade) <= evaluate(first * second, SUPPORT, grade)


@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100),
)
def test_semiring_laws_on_declared_domains(a, b, c):
    """Four readings obey identities, annihilation, associativity and distribution.

    Viterbi laws use exact rationals; production floats approximate that model.
    """
    exact_confidence = Semiring(Fraction(0), Fraction(1), max, lambda x, y: x * y)
    cases = [
        (BOOLEAN, tuple(bool(v % 2) for v in (a, b, c))),
        (SUPPORT, tuple(Support(v % 5) for v in (a, b, c))),
        (COST, tuple(float(v) for v in (a, b, c))),
        (exact_confidence, tuple(Fraction(v, 100) for v in (a, b, c))),
    ]
    for s, (x, y, z) in cases:
        assert s.add(x, s.zero) == s.add(s.zero, x) == x
        assert s.mul(x, s.one) == s.mul(s.one, x) == x
        assert s.mul(x, s.zero) == s.mul(s.zero, x) == s.zero
        assert s.add(x, y) == s.add(y, x)
        assert s.add(s.add(x, y), z) == s.add(x, s.add(y, z))
        assert s.mul(s.mul(x, y), z) == s.mul(x, s.mul(y, z))
        assert s.mul(x, s.add(y, z)) == s.add(s.mul(x, y), s.mul(x, z))
        assert s.mul(s.add(x, y), z) == s.add(s.mul(x, z), s.mul(y, z))


def test_cost_selects_cheapest_derivation_and_sums_joint_premises():
    costs = {"a": 5.0, "b": 2.0, "c": 1.0}
    assert evaluate(obs("a") + obs("b") * obs("c"), COST, costs.__getitem__) == 3.0
    assert evaluate(ZERO, COST, costs.__getitem__) == float("inf")
    assert evaluate(ONE, COST, costs.__getitem__) == 0.0
