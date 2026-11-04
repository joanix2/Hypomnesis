"""Bridges between Hypomnesis values and the outside world (M3, domain-agnostic).

* :func:`to_json` turns a runtime value into JSON, so that a language (M2) builds
  command payloads as typed Hypomnesis records and the engine sends them through
  the contracts: records become objects, lists and tuples arrays; constructors become
  ``{"tag": ..., "arg": ...}``.
* :func:`to_problem` turns a ``Problem.problem`` value (standard library) into
  the solver-independent Problem IR.
"""

from __future__ import annotations

from fractions import Fraction
from math import isfinite
from typing import Any, Literal

from hypomnesis.ir.problem import (
    Action,
    Constraint,
    Problem,
    Solution,
    State,
    Transition,
    Variable,
    check_assignment,
)
from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.json import value_to_data
from hypomnesis.runtime.values import RecordValue, Value, Variant, from_iterable, iter_list


class BridgeError(ValueError):
    pass


def to_json(value: Value) -> Any:
    try:
        return value_to_data(value)
    except EvaluationError as exc:
        raise BridgeError(str(exc)) from exc


def option(value: Variant) -> Value | None:
    return value.arg if value.tag == "Some" else None


def _number(x: Value) -> Fraction:
    return Fraction(str(x))


def to_problem(value: Value) -> Problem:
    """``Problem.problem`` (Hypomnesis) → :class:`hypomnesis.ir.problem.Problem`."""
    try:
        return _to_problem(value)
    except ValueError as exc:
        raise BridgeError(str(exc)) from exc


def _to_problem(value: Value) -> Problem:
    if not isinstance(value, RecordValue):
        raise BridgeError("Problem.problem attendu")
    sorts: dict[str, Literal["real", "int", "bool"]] = {}
    typed = value.type_name == "Problem.typed_problem"
    if typed:
        kinds: dict[str, Literal["real", "int", "bool"]] = {
            "Real": "real",
            "Integer": "int",
            "Boolean": "bool",
        }
        for name, kind in iter_list(value.get("sorts")):
            if name in sorts or kind.tag not in kinds:
                raise BridgeError("duplicate or unknown variable sort")
            sorts[name] = kinds[kind.tag]
        value = value.get("numeric")
    planning = value if value.type_name == "Problem.planning_problem" else None
    if planning is not None:
        value = planning.get("base_problem")
    variables = []
    for v in iter_list(value.get("variables")):
        lower, upper = option(v.get("lower")), option(v.get("upper"))
        name = v.get("name")
        if typed and name not in sorts:
            raise BridgeError(f"missing variable sort: {name}")
        kind = sorts[name] if typed else "real"
        choices = tuple(_number(c) for c in iter_list(v.get("choices")))
        if kind == "bool" and any(c not in (0, 1) for c in choices):
            raise BridgeError("boolean numeric choices must be 0 or 1")
        variables.append(
            Variable(
                name,
                lower=None if lower is None else _number(lower),
                upper=None if upper is None else _number(upper),
                choices=tuple(bool(c) for c in choices) if kind == "bool" else choices,
                kind=kind,
            )
        )
    if typed and set(sorts) != {v.name for v in variables}:
        raise BridgeError("unknown variable sort")
    relations = {"Le": "<=", "Ge": ">=", "Eq": "=="}
    constraints = tuple(
        Constraint(
            c.get("label"),
            tuple((name, _number(k)) for name, k in iter_list(c.get("terms"))),
            relations[c.get("relation").tag],
            _number(c.get("bound")),
        )
        for c in iter_list(value.get("constraints"))
    )
    target = option(value.get("target"))
    return Problem(
        tuple(variables),
        constraints,
        None if target is None else (target[0], _number(target[1])),
        states=()
        if planning is None
        else tuple(
            State(s.get("state_id"), tuple((n, _number(x)) for n, x in iter_list(s.get("values"))))
            for s in iter_list(planning.get("states"))
        ),
        actions=()
        if planning is None
        else tuple(
            Action(
                a.get("action_id"),
                tuple(
                    Constraint(
                        c.get("label"),
                        tuple((n, _number(x)) for n, x in iter_list(c.get("terms"))),
                        relations[c.get("relation").tag],
                        _number(c.get("bound")),
                    )
                    for c in iter_list(a.get("preconditions"))
                ),
                tuple((n, _number(x)) for n, x in iter_list(a.get("effects"))),
            )
            for a in iter_list(planning.get("actions"))
        ),
        transitions=()
        if planning is None
        else tuple(
            Transition(
                t.get("transition_id"), t.get("from_state"), t.get("action_ref"), t.get("to_state")
            )
            for t in iter_list(planning.get("transitions"))
        ),
    )


def solution_value(problem: Problem, solution: Solution) -> RecordValue:
    """Recheck a solver certificate before returning exact nominal language values."""
    verdicts = {"sat": ("Sat", 0), "unsat": ("Unsat", 1), "unknown": ("Unknown", 2)}
    if solution.status not in verdicts:
        raise BridgeError(f"unknown solver status: {solution.status}")
    if not isfinite(solution.duration_ms) or solution.duration_ms < 0:
        raise BridgeError("invalid solver duration")
    if solution.status == "sat":
        violations = check_assignment(problem, solution.assignment)
        if solution.violations or violations:
            raise BridgeError(f"invalid solver assignment: {solution.violations or violations}")
    elif solution.assignment:
        raise BridgeError("only a sat result may carry an assignment")
    assignment = []
    for variable in problem.variables:
        if solution.status != "sat":
            break
        value = solution.assignment[variable.name]
        if variable.kind == "bool":
            scalar = Variant("BooleanValue", value, 2)
        elif variable.kind == "int":
            scalar = Variant("IntegerValue", int(value), 1)
        else:
            number = Fraction(str(value)) if isinstance(value, float) else Fraction(value)
            scalar = Variant("Rational", (number.numerator, number.denominator), 0)
        assignment.append((variable.name, scalar))
    tag, index = verdicts[solution.status]
    return RecordValue(
        "Problem.solution",
        (
            ("verdict", Variant(tag, None, index)),
            ("assignment", from_iterable(assignment)),
            ("duration_ms", solution.duration_ms),
            (
                "reason",
                Variant("Some", solution.reason, 1)
                if solution.reason
                else Variant("None", None, 0),
            ),
        ),
    )
