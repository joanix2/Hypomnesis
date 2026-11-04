import json
import math
from fractions import Fraction

import pytest
import z3
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.backends import z3_solver
from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.engine.bridge import BridgeError, solution_value, to_problem
from hypomnesis.ir.problem import (
    Action,
    Constraint,
    Problem,
    Solution,
    State,
    Variable,
    check_assignment,
)
from hypomnesis.runtime.values import iter_list
from hypomnesis.session import Session


def mixed():
    return Problem(
        (Variable("i", 0, 5, kind="int"), Variable("r"), Variable("b", kind="bool")),
        (
            Constraint("integer", (("i", 1),), "==", 2),
            Constraint("rational", (("r", 3),), "==", 1),
            Constraint("boolean", (("b", 1),), "==", 1),
        ),
    )


def test_three_sorts_exact_assignment_and_typed_language_model():
    problem = mixed()
    result = z3_solver.solve(problem)
    assert result.status == "sat" and result.assignment == {"i": 2, "r": Fraction(1, 3), "b": True}
    assert type(result.assignment["i"]) is int and type(result.assignment["b"]) is bool
    assert not result.violations and not check_assignment(problem, result.assignment)
    assert math.isfinite(result.duration_ms) and result.duration_ms >= 0
    value = solution_value(problem, result)
    session = Session()
    encoded = TypeCodec(session.checker, "Problem.solution").encode(value)
    assert encoded["verdict"] == {"tag": "Sat"}
    assert dict(iter_list(value.get("assignment")))["r"].arg == (1, 3)
    assert dict(iter_list(value.get("assignment")))["i"].tag == "IntegerValue"
    assert dict(iter_list(value.get("assignment")))["b"].tag == "BooleanValue"


@given(goal=st.integers(-100, 100))
def test_integer_sort_does_not_relax_to_fractional_reals(goal):
    p = Problem(
        (Variable("x", kind="int"),),
        (Constraint("half-integer", (("x", 2),), "==", 2 * goal + 1),),
    )
    assert z3_solver.solve(p).status == "unsat"


def test_mixed_roundtrip_and_legacy_json_reading():
    p = mixed()
    assert Problem.from_json(json.loads(json.dumps(p.to_json()))) == p
    legacy = Problem((Variable("x"),), ()).to_json()
    legacy["version"] = "1.0.0"
    del legacy["variables"][0]["kind"]
    assert Problem.from_json(legacy) == Problem((Variable("x"),), ())
    states = Problem(
        (Variable("b", kind="bool"),),
        (),
        states=(State("off", (("b", False),)),),
        actions=(Action("enable", effects=(("b", True),)),),
    )
    assert Problem.from_json(states.to_json()) == states


@pytest.mark.parametrize(
    "assignment",
    [
        {"i": Fraction(3, 2), "r": Fraction(1, 3), "b": True},
        {"i": 2, "r": Fraction(1, 3), "b": 1},
        {"i": True, "r": Fraction(1, 3), "b": True},
        {"i": 2, "r": Fraction(1, 3), "b": True, "extra": 0},
        {"i": 2, "r": float("nan"), "b": True},
        {"i": 2, "r": Fraction(1, 3)},
    ],
)
def test_altered_models_are_independently_refused(assignment):
    p = mixed()
    assert check_assignment(p, assignment)
    with pytest.raises(BridgeError, match="invalid solver assignment"):
        solution_value(p, Solution("sat", assignment))


def test_boolean_choices_and_numeric_zero_one_semantics():
    p = Problem(
        (Variable("b", choices=(False,), kind="bool"), Variable("x", kind="int")),
        (Constraint("coupled", (("b", 2), ("x", 1)), "==", 3),),
    )
    result = z3_solver.solve(p)
    assert result.assignment == {"b": False, "x": 3}
    assert not check_assignment(p, result.assignment)


@pytest.mark.parametrize(
    "make",
    [
        lambda: Variable("x", kind="unsupported"),
        lambda: Variable("x", lower=0, kind="bool"),
        lambda: Variable("x", choices=(1,), kind="bool"),
        lambda: Variable("x", choices=(True,), kind="int"),
        lambda: Variable("x", lower=0.5, kind="int"),
        lambda: Problem((Variable("b", kind="bool"),), (), target=("b", 1)),
        lambda: Problem((Variable("b", kind="bool"),), (), states=(State("s", (("b", 1),)),)),
    ],
)
def test_invalid_domains_are_rejected(make):
    with pytest.raises(ValueError):
        make()


def test_fresh_objective_variable_does_not_collide_with_user_variables():
    p = Problem(
        (Variable("x"), Variable("__gap_x", choices=(-1,))),
        (),
        target=("x", Fraction(1, 3)),
    )
    result = z3_solver.solve(p)
    assert result.status == "sat" and result.assignment["x"] == Fraction(1, 3)


def test_unknown_duration_reason_and_timeout_are_explicit(monkeypatch):
    instance = z3.Optimize()
    monkeypatch.setattr(instance, "check", lambda: z3.unknown)
    monkeypatch.setattr(instance, "reason_unknown", lambda: "timeout")
    monkeypatch.setattr(z3_solver.z3, "Optimize", lambda: instance)
    result = z3_solver.solve(Problem((), ()), timeout_ms=10)
    assert result.status == "unknown" and result.reason == "timeout"
    assert result.duration_ms >= 0 and not result.assignment
    value = solution_value(Problem((), ()), result)
    assert value.get("verdict").tag == "Unknown" and value.get("reason").arg == "timeout"


@pytest.mark.parametrize("timeout", [0, -1, True, 1.5])
def test_bad_timeout_is_not_silently_ignored(timeout):
    with pytest.raises(ValueError, match="timeout"):
        z3_solver.solve(Problem((), ()), timeout_ms=timeout)


def test_typed_hypomnesis_wrapper_refuses_incomplete_sort_maps():
    session = Session()
    session.load("""
let numeric = {
  Problem.variables = [
    { Problem.name = "b"; lower = None; upper = None; choices = [] }
  ]; constraints = []; target = None
}
let typed = { Problem.numeric = numeric; sorts = [("b", Problem.Boolean)] }
let incomplete = { typed with sorts = [] }
let duplicate = { typed with sorts = [("b", Problem.Boolean); ("b", Problem.Boolean)] }
let extra = { typed with sorts = [("b", Problem.Boolean); ("extra", Problem.Real)] }
""")
    assert to_problem(session.value("typed")).variables[0].kind == "bool"
    for symbol in ("incomplete", "duplicate", "extra"):
        with pytest.raises(BridgeError, match="sort"):
            to_problem(session.value(symbol))
