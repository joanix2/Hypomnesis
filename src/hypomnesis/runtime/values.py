"""Runtime values.

Scalars map to Python values (``int``, ``float``, ``str``, ``bool``); unit is
the empty tuple and tuples are Python tuples. Lists are ordinary variants
built from the ``[]`` and ``::`` constructors.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from typing import Any

from hypomnesis.language.errors import EvaluationError

Value = Any
UNIT: tuple = ()


@dataclass(frozen=True, slots=True)
class Variant:
    tag: str
    arg: Value = None
    index: int = field(default=0, compare=False)


@dataclass(frozen=True, slots=True)
class RecordValue:
    type_name: str
    fields: tuple[tuple[str, Value], ...]

    def get(self, name: str) -> Value:
        for key, value in self.fields:
            if key == name:
                return value
        raise EvaluationError(f"record has no field {name}")

    def update(self, changes: dict[str, Value]) -> RecordValue:
        return RecordValue(self.type_name, tuple((k, changes.get(k, v)) for k, v in self.fields))


class Function:
    """Common base for applicable values."""

    __slots__ = ()
    arity: int
    name: str


class Closure(Function):
    __slots__ = ("arity", "body", "env", "name", "params")

    def __init__(self, params: tuple[str, ...], body: Callable, env, name: str) -> None:
        self.params = params
        self.arity = len(params)
        self.body = body
        self.env = env
        self.name = name


class Native(Function):
    __slots__ = ("arity", "fn", "name")

    def __init__(self, name: str, arity: int, fn: Callable[..., Value]) -> None:
        self.name = name
        self.arity = arity
        self.fn = fn


class Partial(Function):
    __slots__ = ("args", "arity", "fn", "name")

    def __init__(self, fn: Function, args: tuple[Value, ...]) -> None:
        self.fn = fn
        self.args = args
        self.arity = fn.arity - len(args)
        self.name = fn.name


NIL = Variant("[]", None, 0)


def cons(head: Value, tail: Value) -> Variant:
    return Variant("::", (head, tail), 1)


def from_iterable(items: Iterable[Value]) -> Variant:
    result = NIL
    for item in reversed(list(items)):
        result = cons(item, result)
    return result


def iter_list(value: Variant) -> Iterator[Value]:
    while value.tag == "::":
        head, value = value.arg
        yield head


def is_list(value: Value) -> bool:
    return isinstance(value, Variant) and value.tag in ("[]", "::")


# ---------------------------------------------------------------- printing


def show(value: Value) -> str:
    """OCaml-like rendering of a runtime value."""
    return _show(value, top=True)


def _show(v: Value, top: bool = False) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v) if top or v >= 0 else f"({v})"
    if isinstance(v, float):
        text = repr(v)
        if text.endswith(".0"):
            text = text[:-1]
        return text if top or v >= 0 else f"({text})"
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'
    if v == UNIT and isinstance(v, tuple):
        return "()"
    if isinstance(v, tuple):
        return "(" + ", ".join(_show(x, True) for x in v) + ")"
    if is_list(v):
        return "[" + "; ".join(_show(x, True) for x in iter_list(v)) + "]"
    if isinstance(v, Variant):
        if v.arg is None:
            return v.tag
        text = f"{v.tag} {_show(v.arg)}"
        return text if top else f"({text})"
    if isinstance(v, RecordValue):
        return "{" + "; ".join(f"{k} = {_show(x, True)}" for k, x in v.fields) + "}"
    if isinstance(v, Function):
        return "<fun>"
    return repr(v)
