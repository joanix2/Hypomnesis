import json
from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.backends.z3_solver import solve
from hypomnesis.contracts.registry import ContractError, SchemaRegistry
from hypomnesis.engine.bridge import BridgeError, to_problem
from hypomnesis.ir.problem import (
    SCHEMA_ID,
    Action,
    Constraint,
    Problem,
    State,
    Transition,
    Variable,
    check_assignment,
)
from hypomnesis.session import Session


def example():
    return Problem(
        (Variable("thickness", 1, 10),),
        (Constraint("rigidity", (("thickness", 3),), ">=", 9),),
        ("thickness", Fraction(10, 3)),
        states=(State("initial", (("thickness", 2),)), State("final", (("thickness", 4),))),
        actions=(Action("resize", effects=(("thickness", 4),)),),
        transitions=(Transition("increase", "initial", "resize", "final"),),
    )


def test_json_roundtrip_and_solver():
    p = example()
    document = json.loads(json.dumps(p.to_json(), allow_nan=False))
    SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, document)
    assert Problem.from_json(document) == p
    result = solve(p)
    assert result.status == "sat"
    assert check_assignment(p, result.assignment) == []
    assert result.assignment["thickness"] == Fraction(10, 3)
    with pytest.raises(FrozenInstanceError):
        p.states[0].name = "mutated"


@given(st.integers(), st.integers(min_value=1))
def test_exact_rational_json(n, d):
    p = Problem((Variable("x", choices=(Fraction(n, d),)),), (), ("x", Fraction(n, d)))
    assert Problem.from_json(json.loads(json.dumps(p.to_json()))) == p


@pytest.mark.parametrize(
    "construct",
    [
        lambda: Variable("", 0, 1),
        lambda: Variable("x", 2, 1),
        lambda: Variable("x", choices=(True,)),
        lambda: Variable("x", choices=(float("nan"),)),
        lambda: Variable("x", 0, 1, (2,)),
        lambda: Variable("x", choices=[1]),
        lambda: Constraint("c", (("x", 1),), "!", 1),
        lambda: Problem((Variable("x"), Variable("x")), ()),
        lambda: Problem((), (Constraint("c", (("missing", 1),), "==", 1),)),
        lambda: Problem((), (), ("missing", 1)),
        lambda: Problem((), (), transitions=(Transition("t", "a", "act", "b"),)),
        lambda: Problem((Variable("x", 0, 1),), (), states=(State("s", (("x", 2),)),)),
    ],
)
def test_invalid_structures(construct):
    with pytest.raises(ValueError):
        construct()


def test_invalid_json_and_assignment():
    document = example().to_json()
    document["variables"][0]["lower"]["denominator"] = 0
    with pytest.raises(ContractError):
        Problem.from_json(document)
    document = example().to_json()
    document["unexpected"] = True
    with pytest.raises(ContractError):
        Problem.from_json(document)
    assert check_assignment(example(), {"thickness": True})
    assert check_assignment(example(), {})
    document = example().to_json()
    document["variables"][0]["lower"]["numerator"] = 1.0
    with pytest.raises(ValueError, match="JSON integers"):
        Problem.from_json(document)
    decimal = Problem((Variable("x"),), (Constraint("decimal", (("x", 1),), "==", 0.1),))
    assert check_assignment(decimal, {"x": 0.1}) == []


def test_construct_plan_from_language():
    session = Session()
    session.load("""
    let variable : Problem.variable = {
      Problem.name = "thickness"; lower = Some 1.0; upper = Some 10.0; choices = []
    }
    let rigidity : Problem.constraint = {
      Problem.label = "rigidity"; terms = [("thickness", 3.0)]; relation = Problem.Ge; bound = 9.0
    }
    let base : Problem.problem = {
      Problem.variables = [variable]; constraints = [rigidity]; target = Some ("thickness", 4.0)
    }
    let start : Problem.state = { Problem.state_id = "initial"; values = [("thickness", 2.0)] }
    let stop : Problem.state = { Problem.state_id = "final"; values = [("thickness", 4.0)] }
    let action : Problem.action = {
      Problem.action_id = "resize"; preconditions = []; effects = [("thickness", 4.0)]
    }
    let transition : Problem.transition = {
      Problem.transition_id = "increase";
      from_state = "initial"; action_ref = "resize"; to_state = "final"
    }
    let plan : Problem.planning_problem = {
      Problem.base_problem = base; states = [start; stop];
      actions = [action]; transitions = [transition]
    }
    """)
    p = to_problem(session.value("plan"))
    assert len(p.transitions) == 1
    assert p.actions[0].effects == (("thickness", 4),)
    assert not check_assignment(p, {"thickness": 4})
    session.load('let invalid = { base with target = Some ("missing", 1.0) }')
    with pytest.raises(BridgeError, match="undefined"):
        to_problem(session.value("invalid"))
