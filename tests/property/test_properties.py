"""Property-based checks: the interpreter agrees with Python on core data."""

from hypothesis import given, settings
from hypothesis import strategies as st

from hypomnesis.runtime.values import from_iterable, iter_list
from hypomnesis.session import Session

SESSION = Session()
small_ints = st.integers(min_value=-(10**6), max_value=10**6)


def call(path: str, *args):
    return SESSION.interpreter.apply(SESSION.value(path), list(args))


@settings(max_examples=50, deadline=None)
@given(st.lists(small_ints, max_size=40))
def test_sort_matches_python(xs):
    result = call("List.sort", SESSION.value("compare"), from_iterable(xs))
    assert list(iter_list(result)) == sorted(xs)


@settings(max_examples=50, deadline=None)
@given(st.lists(small_ints, max_size=40))
def test_rev_is_an_involution_and_length_is_preserved(xs):
    lst = from_iterable(xs)
    assert call("List.rev", call("List.rev", lst)) == lst
    assert call("List.length", lst) == len(xs)


@settings(max_examples=100, deadline=None)
@given(small_ints, small_ints.filter(lambda b: b != 0))
def test_integer_division_truncates_like_ocaml(a, b):
    q, r = call("/", a, b), call("mod", a, b)
    assert q * b + r == a
    assert abs(r) < abs(b)
    assert r == 0 or (r > 0) == (a > 0)


@settings(max_examples=50, deadline=None)
@given(st.lists(small_ints, max_size=20), st.lists(small_ints, max_size=20))
def test_structural_compare_matches_python_on_lists(xs, ys):
    c = call("compare", from_iterable(xs), from_iterable(ys))
    assert (c > 0) - (c < 0) == (xs > ys) - (xs < ys)
