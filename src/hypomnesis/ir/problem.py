"""Problem IR (cahier des charges §8.2, §13.3): variables, domains, linear
constraints and an objective, independent of any solver.

A solver proposes an assignment; :func:`check_assignment` re-checks it by plain
evaluation, independently of the solver (note M3 §4.5: a plugin returns a
certificate, the kernel checks it). Only checked solutions become knowledge.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry

Number = int | float | Fraction
SCHEMA_ID = "https://schemas.example.org/hypomnesis/problem/1.0.0"


def _number(value: Number) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction)):
        raise ValueError(f"expected a finite number, got {value!r}")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite number")
        return Fraction(str(value))
    return Fraction(value)


def _name(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("empty or invalid identifier")


def _unique(names: list[str]) -> None:
    for name in names:
        _name(name)
    if len(set(names)) != len(names):
        raise ValueError("duplicate identifier")


def _pairs(values: tuple[tuple[str, Number], ...]) -> tuple[tuple[str, Fraction], ...]:
    if not isinstance(values, tuple) or any(
        not isinstance(pair, tuple) or len(pair) != 2 for pair in values
    ):
        raise ValueError("expected an immutable tuple of name/number pairs")
    _unique([name for name, _ in values])
    return tuple((name, _number(value)) for name, value in values)


def _tuple(values: tuple, item_type: type) -> None:
    if not isinstance(values, tuple) or any(not isinstance(v, item_type) for v in values):
        raise ValueError(f"expected an immutable tuple of {item_type.__name__}")


@dataclass(frozen=True)
class Variable:
    name: str
    lower: Number | None = None
    upper: Number | None = None
    #: Allowed values (a discrete domain, e.g. standard sheet thicknesses).
    choices: tuple[Number, ...] = ()

    def __post_init__(self) -> None:
        _name(self.name)
        if not isinstance(self.choices, tuple):
            raise ValueError("choices must be immutable")
        for field_name in ("lower", "upper"):
            value = getattr(self, field_name)
            if value is not None:
                object.__setattr__(self, field_name, _number(value))
        choices = tuple(_number(value) for value in self.choices)
        object.__setattr__(self, "choices", choices)
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError("inverted domain bounds")
        if len(set(choices)) != len(choices):
            raise ValueError("duplicate domain choice")
        if any(
            (self.lower is not None and x < self.lower)
            or (self.upper is not None and x > self.upper)
            for x in choices
        ):
            raise ValueError("choice outside domain bounds")


@dataclass(frozen=True)
class Constraint:
    """``sum(coeff * var) op rhs`` with op in ``<=``, ``>=``, ``==``."""

    label: str
    terms: tuple[tuple[str, Number], ...]
    op: str
    rhs: Number

    def __post_init__(self) -> None:
        _name(self.label)
        if self.op not in ("<=", ">=", "=="):
            raise ValueError(f"unsupported relation: {self.op}")
        object.__setattr__(self, "terms", _pairs(self.terms))
        object.__setattr__(self, "rhs", _number(self.rhs))

    def holds(self, assignment: dict[str, Number]) -> bool:
        lhs = sum(Fraction(c) * Fraction(assignment[v]) for v, c in self.terms)
        rhs = Fraction(self.rhs)
        return {"<=": lhs <= rhs, ">=": lhs >= rhs, "==": lhs == rhs}[self.op]


@dataclass(frozen=True)
class State:
    name: str
    values: tuple[tuple[str, Number], ...] = ()

    def __post_init__(self) -> None:
        _name(self.name)
        object.__setattr__(self, "values", _pairs(self.values))


@dataclass(frozen=True)
class Action:
    name: str
    preconditions: tuple[Constraint, ...] = ()
    effects: tuple[tuple[str, Number], ...] = ()

    def __post_init__(self) -> None:
        _name(self.name)
        _tuple(self.preconditions, Constraint)
        _unique([c.label for c in self.preconditions])
        object.__setattr__(self, "effects", _pairs(self.effects))


@dataclass(frozen=True)
class Transition:
    name: str
    source: str
    action: str
    target: str

    def __post_init__(self) -> None:
        for value in (self.name, self.source, self.action, self.target):
            _name(value)


@dataclass(frozen=True)
class Problem:
    variables: tuple[Variable, ...]
    constraints: tuple[Constraint, ...]
    #: Objective: minimise the distance between ``target[0]`` and ``target[1]``.
    target: tuple[str, Number] | None = None
    description: str = ""
    states: tuple[State, ...] = ()
    actions: tuple[Action, ...] = ()
    transitions: tuple[Transition, ...] = ()

    def __post_init__(self) -> None:
        for items, kind in (
            (self.variables, Variable),
            (self.constraints, Constraint),
            (self.states, State),
            (self.actions, Action),
            (self.transitions, Transition),
        ):
            _tuple(items, kind)
        _unique([v.name for v in self.variables])
        _unique([c.label for c in self.constraints])
        _unique([s.name for s in self.states])
        _unique([a.name for a in self.actions])
        _unique([t.name for t in self.transitions])
        names = {v.name for v in self.variables}
        references = [n for c in self.constraints for n, _ in c.terms]
        references += [n for s in self.states for n, _ in s.values]
        references += [n for a in self.actions for n, _ in a.effects]
        references += [n for a in self.actions for c in a.preconditions for n, _ in c.terms]
        if self.target is not None:
            if not isinstance(self.target, tuple) or len(self.target) != 2:
                raise ValueError("objective must be a variable/target pair")
            name, goal = self.target
            references.append(name)
            object.__setattr__(self, "target", (name, _number(goal)))
        if any(name not in names for name in references):
            raise ValueError("undefined variable reference")
        states = {s.name for s in self.states}
        actions = {a.name for a in self.actions}
        if any(
            t.source not in states or t.target not in states or t.action not in actions
            for t in self.transitions
        ):
            raise ValueError("undefined state or action reference")
        if not isinstance(self.description, str):
            raise ValueError("description must be a string")
        variables = {v.name: v for v in self.variables}
        for pairs in (
            *(s.values for s in self.states),
            *(a.effects for a in self.actions),
        ):
            for name, value in pairs:
                variable = variables[name]
                if (
                    (variable.lower is not None and value < variable.lower)
                    or (variable.upper is not None and value > variable.upper)
                    or (variable.choices and value not in variable.choices)
                ):
                    raise ValueError(f"{name}: state/effect outside domain")

    def to_json(self) -> dict[str, Any]:
        def number(n: Number) -> dict[str, int]:
            q = _number(n)
            return {"numerator": q.numerator, "denominator": q.denominator}

        def pairs(xs: tuple[tuple[str, Number], ...]) -> list[list[Any]]:
            return [[name, number(n)] for name, n in xs]

        def constraint(c: Constraint) -> dict[str, Any]:
            return {"label": c.label, "terms": pairs(c.terms), "op": c.op, "rhs": number(c.rhs)}

        return {
            "version": "1.0.0",
            "description": self.description,
            "variables": [
                {
                    "name": v.name,
                    "lower": None if v.lower is None else number(v.lower),
                    "upper": None if v.upper is None else number(v.upper),
                    "choices": [number(n) for n in v.choices],
                }
                for v in self.variables
            ],
            "constraints": [constraint(c) for c in self.constraints],
            "target": None if self.target is None else [self.target[0], number(self.target[1])],
            "states": [{"name": s.name, "values": pairs(s.values)} for s in self.states],
            "actions": [
                {
                    "name": a.name,
                    "preconditions": [constraint(c) for c in a.preconditions],
                    "effects": pairs(a.effects),
                }
                for a in self.actions
            ],
            "transitions": [
                {"name": t.name, "source": t.source, "action": t.action, "target": t.target}
                for t in self.transitions
            ],
        }

    @classmethod
    def from_json(cls, document: Any) -> Problem:
        SchemaRegistry.with_builtin_schemas().validate(SCHEMA_ID, document)

        def number(n: dict[str, int]) -> Fraction:
            return Fraction(n["numerator"], n["denominator"])

        def pairs(xs: list) -> tuple[tuple[str, Number], ...]:
            return tuple((name, number(n)) for name, n in xs)

        def constraint(c: dict[str, Any]) -> Constraint:
            return Constraint(c["label"], pairs(c["terms"]), c["op"], number(c["rhs"]))

        return cls(
            variables=tuple(
                Variable(
                    v["name"],
                    None if v["lower"] is None else number(v["lower"]),
                    None if v["upper"] is None else number(v["upper"]),
                    tuple(number(n) for n in v["choices"]),
                )
                for v in document["variables"]
            ),
            constraints=tuple(constraint(c) for c in document["constraints"]),
            target=None
            if document["target"] is None
            else (document["target"][0], number(document["target"][1])),
            description=document["description"],
            states=tuple(State(s["name"], pairs(s["values"])) for s in document["states"]),
            actions=tuple(
                Action(
                    a["name"], tuple(constraint(c) for c in a["preconditions"]), pairs(a["effects"])
                )
                for a in document["actions"]
            ),
            transitions=tuple(Transition(**t) for t in document["transitions"]),
        )


@dataclass(frozen=True)
class Solution:
    status: str  # "sat" | "unsat" | "unknown"
    assignment: dict[str, Number] = field(default_factory=dict)
    solver: str = ""
    #: Constraints violated by the proposed assignment (empty when it checks).
    violations: tuple[str, ...] = ()


def check_assignment(problem: Problem, assignment: dict[str, Number]) -> list[str]:
    """Labels of what the assignment violates: bounds, domains, constraints."""
    problems = []
    for v in problem.variables:
        if v.name not in assignment:
            problems.append(f"{v.name} sans valeur")
            continue
        try:
            x = _number(assignment[v.name])
        except ValueError as exc:
            problems.append(f"{v.name}: {exc}")
            continue
        if v.lower is not None and x < Fraction(v.lower):
            problems.append(f"{v.name} < {v.lower}")
        if v.upper is not None and x > Fraction(v.upper):
            problems.append(f"{v.name} > {v.upper}")
        if v.choices and x not in {Fraction(c) for c in v.choices}:
            problems.append(f"{v.name} hors de {list(v.choices)}")
    if problems:
        return problems
    return [c.label for c in problem.constraints if not c.holds(assignment)]
