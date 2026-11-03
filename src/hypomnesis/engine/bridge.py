"""Bridges between Hypomnesis values and the outside world (M3, domain-agnostic).

* :func:`to_json` turns a runtime value into JSON, so that a language (M2) builds
  command payloads as typed Hypomnesis records and the engine sends them through
  the contracts: records become objects, lists and tuples arrays, ``Some x``
  becomes ``x`` and ``None`` ``null``; other constructors become
  ``{"tag": ..., "arg": ...}``.
* :func:`to_problem` turns a ``Problem.problem`` value (standard library) into
  the solver-independent Problem IR.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from hypomnesis.ir.problem import Constraint, Problem, Variable
from hypomnesis.runtime.values import Function, RecordValue, Value, Variant, is_list, iter_list


class BridgeError(ValueError):
    pass


def to_json(value: Value) -> Any:
    if isinstance(value, bool | int | float | str):
        return value
    if value == () and isinstance(value, tuple):
        return None
    if isinstance(value, tuple):
        return [to_json(v) for v in value]
    if isinstance(value, RecordValue):
        return {k: to_json(v) for k, v in value.fields}
    if is_list(value):
        return [to_json(v) for v in iter_list(value)]
    if isinstance(value, Variant):
        if value.tag == "None":
            return None
        if value.tag == "Some":
            return to_json(value.arg)
        return (
            {"tag": value.tag}
            if value.arg is None
            else {"tag": value.tag, "arg": to_json(value.arg)}
        )
    if isinstance(value, Function):
        raise BridgeError("une fonction n'a pas de représentation JSON")
    raise BridgeError(f"valeur inattendue {value!r}")


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
