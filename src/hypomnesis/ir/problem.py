"""Problem IR (cahier des charges §8.2, §13.3): variables, domains, linear
constraints and an objective, independent of any solver.

A solver proposes an assignment; :func:`check_assignment` re-checks it by plain
evaluation, independently of the solver (note M3 §4.5: a plugin returns a
certificate, the kernel checks it). Only checked solutions become knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

Number = int | float | Fraction


@dataclass(frozen=True)
class Variable:
    name: str
    lower: Number | None = None
    upper: Number | None = None
    #: Allowed values (a discrete domain, e.g. standard sheet thicknesses).
    choices: tuple[Number, ...] = ()


@dataclass(frozen=True)
class Constraint:
    """``sum(coeff * var) op rhs`` with op in ``<=``, ``>=``, ``==``."""

    label: str
    terms: tuple[tuple[str, Number], ...]
    op: str
    rhs: Number

    def holds(self, assignment: dict[str, Number]) -> bool:
        lhs = sum(Fraction(c) * Fraction(assignment[v]) for v, c in self.terms)
        rhs = Fraction(self.rhs)
        return {"<=": lhs <= rhs, ">=": lhs >= rhs, "==": lhs == rhs}[self.op]


@dataclass(frozen=True)
class Problem:
    variables: tuple[Variable, ...]
    constraints: tuple[Constraint, ...]
    #: Objective: minimise the distance between ``target[0]`` and ``target[1]``.
    target: tuple[str, Number] | None = None
    description: str = ""


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
        x = Fraction(assignment[v.name])
        if v.lower is not None and x < Fraction(v.lower):
            problems.append(f"{v.name} < {v.lower}")
        if v.upper is not None and x > Fraction(v.upper):
            problems.append(f"{v.name} > {v.upper}")
        if v.choices and x not in {Fraction(c) for c in v.choices}:
            problems.append(f"{v.name} hors de {list(v.choices)}")
    if problems:
        return problems
    return [c.label for c in problem.constraints if not c.holds(assignment)]
