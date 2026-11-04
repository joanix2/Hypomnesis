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
from typing import Any

from hypomnesis.ir.problem import Constraint, Problem, Variable
from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.json import value_to_data
from hypomnesis.runtime.values import RecordValue, Value, Variant, iter_list


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
    if not isinstance(value, RecordValue):
        raise BridgeError("Problem.problem attendu")
    variables = []
    for v in iter_list(value.get("variables")):
        lower, upper = option(v.get("lower")), option(v.get("upper"))
        variables.append(
            Variable(
                v.get("name"),
                lower=None if lower is None else _number(lower),
                upper=None if upper is None else _number(upper),
                choices=tuple(_number(c) for c in iter_list(v.get("choices"))),
            )
        )
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
    )
