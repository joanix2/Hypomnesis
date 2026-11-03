"""Registry of native primitives reachable through ``external`` declarations.

Source programs can only bind symbols registered here: there is no way to
reach arbitrary Python from Hypomnesis code. Host applications may register
additional primitives on their own :class:`NativeRegistry`.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.values import UNIT, Function, RecordValue, Value, Variant


@dataclass(frozen=True)
class NativeSpec:
    symbol: str
    arity: int
    fn: Callable[..., Value]


class NativeRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, NativeSpec] = {}

    def register(self, symbol: str, arity: int, fn: Callable[..., Value]) -> None:
        if symbol in self._specs:
            raise ValueError(f"native symbol {symbol!r} is already registered")
        self._specs[symbol] = NativeSpec(symbol, arity, fn)

    def get(self, symbol: str) -> NativeSpec:
        return self._specs[symbol]

    def arities(self) -> dict[str, int]:
        return {s.symbol: s.arity for s in self._specs.values()}

    def copy(self) -> NativeRegistry:
        clone = NativeRegistry()
        clone._specs = dict(self._specs)
        return clone


# ------------------------------------------------------ structural compare


def _check_comparable(v: Value) -> None:
    if isinstance(v, Function):
        raise EvaluationError("compare: functional value")


def compare(a: Value, b: Value) -> int:
    _check_comparable(a)
    if isinstance(a, Variant):
        if a.index != b.index:
            return -1 if a.index < b.index else 1
        if a.arg is None:
            return 0
        return compare(a.arg, b.arg)
    if isinstance(a, RecordValue):
        for (_, x), (_, y) in zip(a.fields, b.fields, strict=True):
            c = compare(x, y)
            if c:
                return c
        return 0
    if isinstance(a, tuple):
        for x, y in zip(a, b, strict=True):
            c = compare(x, y)
            if c:
                return c
        return 0
    if isinstance(a, float) and (math.isnan(a) or math.isnan(b)):
        return 0 if math.isnan(a) and math.isnan(b) else (-1 if math.isnan(a) else 1)
    return -1 if a < b else (1 if a > b else 0)


def equal(a: Value, b: Value) -> bool:
    _check_comparable(a)
    if isinstance(a, Variant):
        return a.tag == b.tag and (a.arg is None or equal(a.arg, b.arg))
    if isinstance(a, RecordValue):
        return all(equal(x, y) for (_, x), (_, y) in zip(a.fields, b.fields, strict=True))
    if isinstance(a, tuple):
        return all(equal(x, y) for x, y in zip(a, b, strict=True))
    return a == b


# ------------------------------------------------------------ primitives


def _int_div(a: int, b: int) -> int:
    if b == 0:
        raise EvaluationError("Division_by_zero")
    q = abs(a) // abs(b)  # truncate toward zero, like OCaml
    return q if (a >= 0) == (b >= 0) else -q


def _int_mod(a: int, b: int) -> int:
    return a - b * _int_div(a, b)


def _float_div(a: float, b: float) -> float:
    if b == 0.0:
        if a == 0.0 or math.isnan(a):
            return math.nan
        return math.copysign(math.inf, a) * math.copysign(1.0, b)
    return a / b


def _float_to_string(x: float) -> str:
    text = repr(x)
    return text[:-1] if text.endswith(".0") else text


def _int_of_string(s: str) -> int:
    try:
        return int(s)
    except ValueError:
        raise EvaluationError(f"int_of_string: invalid input {s!r}") from None


def _float_of_string(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        raise EvaluationError(f"float_of_string: invalid input {s!r}") from None


def _failwith(message: str) -> Value:
    raise EvaluationError(f"Failure: {message}")


def _string_sub(s: str, start: int, length: int) -> str:
    if start < 0 or length < 0 or start + length > len(s):
        raise EvaluationError("String.sub: invalid range")
    return s[start : start + length]


def _string_get(s: str, i: int) -> str:
    if not 0 <= i < len(s):
        raise EvaluationError("String.get: index out of bounds")
    return s[i]


def default_registry() -> NativeRegistry:
    reg = NativeRegistry()
    r = reg.register
    # integers
    r("int.add", 2, lambda a, b: a + b)
    r("int.sub", 2, lambda a, b: a - b)
    r("int.mul", 2, lambda a, b: a * b)
    r("int.div", 2, _int_div)
    r("int.mod", 2, _int_mod)
    r("int.to_string", 1, str)
    r("int.of_string", 1, _int_of_string)
    r("int.to_float", 1, float)
    # floats
    r("float.add", 2, lambda a, b: a + b)
    r("float.sub", 2, lambda a, b: a - b)
    r("float.mul", 2, lambda a, b: a * b)
    r("float.div", 2, _float_div)
    r("float.pow", 2, lambda a, b: math.pow(a, b))
    r("float.sqrt", 1, lambda x: math.sqrt(x) if x >= 0 else math.nan)
    r("float.floor", 1, math.floor)
    r("float.ceil", 1, math.ceil)
    r("float.abs", 1, abs)
    r("float.to_int", 1, int)
    r("float.to_string", 1, _float_to_string)
    r("float.of_string", 1, _float_of_string)
    r("float.pi", 0, lambda: math.pi)
    # strings
    r("string.concat", 2, lambda a, b: a + b)
    r("string.length", 1, len)
    r("string.sub", 3, _string_sub)
    r("string.get", 2, _string_get)
    r("string.uppercase", 1, str.upper)
    r("string.lowercase", 1, str.lower)
    # polymorphic structural comparison
    r("poly.eq", 2, equal)
    r("poly.neq", 2, lambda a, b: not equal(a, b))
    r("poly.lt", 2, lambda a, b: compare(a, b) < 0)
    r("poly.le", 2, lambda a, b: compare(a, b) <= 0)
    r("poly.gt", 2, lambda a, b: compare(a, b) > 0)
    r("poly.ge", 2, lambda a, b: compare(a, b) >= 0)
    r("poly.compare", 2, compare)
    # control
    r("core.failwith", 1, _failwith)
    r("core.ignore", 1, lambda _: UNIT)
    return reg
