"""Type terms, schemes and unification for Hindley-Milner inference.

Type variables are mutable cells (union-find) carrying a binding level, which
gives linear-time generalisation (Rémy's levels). Generalised variables are
represented by :class:`TGen` indices inside a :class:`Scheme`; the same
encoding is used for the parameters of declared types.
"""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from hypomnesis.language.errors import Span, TypeCheckError

_ids = itertools.count()


class Type:
    __slots__ = ()


class TVar(Type):
    __slots__ = ("id", "level", "ref")

    def __init__(self, level: int) -> None:
        self.id = next(_ids)
        self.level = level
        self.ref: Type | None = None

    def __repr__(self) -> str:
        return f"TVar({self.id}, ref={self.ref!r})"


@dataclass(frozen=True, slots=True)
class TCon(Type):
    name: str
    args: tuple[Type, ...] = ()


@dataclass(frozen=True, slots=True)
class TGen(Type):
    index: int


@dataclass(frozen=True, slots=True)
class Scheme:
    arity: int
    body: Type


ARROW = "->"
TUPLE = "*"
INT = TCon("int")
FLOAT = TCon("float")
STRING = TCon("string")
BOOL = TCon("bool")
UNIT = TCon("unit")


def arrow(param: Type, result: Type) -> TCon:
    return TCon(ARROW, (param, result))


def arrows(params: list[Type], result: Type) -> Type:
    for param in reversed(params):
        result = arrow(param, result)
    return result


def list_of(item: Type) -> TCon:
    return TCon("list", (item,))


def tuple_of(items: list[Type]) -> TCon:
    return TCon(TUPLE, tuple(items))


def prune(t: Type) -> Type:
    """Follow bound variables, compressing paths."""
    if isinstance(t, TVar) and t.ref is not None:
        t.ref = prune(t.ref)
        return t.ref
    return t


def mono(t: Type) -> Scheme:
    return Scheme(0, t)


# ------------------------------------------------------------ unification


class UnifyError(Exception):
    pass


def _adjust(var: TVar, t: Type) -> None:
    """Occurs check, lowering levels of variables found in ``t``."""
    t = prune(t)
    if isinstance(t, TVar):
        if t is var:
            raise UnifyError("recursive type")
        t.level = min(t.level, var.level)
    elif isinstance(t, TCon):
        for arg in t.args:
            _adjust(var, arg)


def unify(a: Type, b: Type) -> None:
    a, b = prune(a), prune(b)
    if a is b:
        return
    if isinstance(a, TVar):
        _adjust(a, b)
        a.ref = b
    elif isinstance(b, TVar):
        _adjust(b, a)
        b.ref = a
    elif isinstance(a, TCon) and isinstance(b, TCon):
        if a.name != b.name or len(a.args) != len(b.args):
            raise UnifyError("constructor mismatch")
        for x, y in zip(a.args, b.args, strict=True):
            unify(x, y)
    else:
        raise UnifyError("unexpected type term")


def expect(actual: Type, expected: Type, span: Span | None, what: str = "This expression") -> None:
    """Unify, turning failures into a readable diagnostic."""
    try:
        unify(actual, expected)
    except UnifyError as exc:
        printer = TypePrinter()
        message = (
            f"{what} has type {printer.show(actual)} "
            f"but an expression was expected of type {printer.show(expected)}"
        )
        if str(exc) == "recursive type":
            message += " (the type would be infinite)"
        raise TypeCheckError(message, span) from None


# --------------------------------------------- generalise / instantiate


def generalize(t: Type, level: int) -> Scheme:
    """Quantify every variable whose level is deeper than ``level``."""
    return generalize_vars(t, level)[0]


def generalize_vars(t: Type, level: int) -> tuple[Scheme, tuple[TVar, ...]]:
    """Like :func:`generalize`, also returning the quantified variables:
    ``vars[i]`` is the variable that became ``TGen(i)``."""
    mapping: dict[int, TGen] = {}
    quantified: list[TVar] = []

    def go(t: Type) -> Type:
        t = prune(t)
        if isinstance(t, TVar):
            if t.level > level:
                if t.id not in mapping:
                    mapping[t.id] = TGen(len(mapping))
                    quantified.append(t)
                return mapping[t.id]
            return t
        if isinstance(t, TCon):
            return TCon(t.name, tuple(go(a) for a in t.args)) if t.args else t
        return t

    body = go(t)
    return Scheme(len(mapping), body), tuple(quantified)


def substitute(t: Type, args: Sequence[Type]) -> Type:
    """Replace ``TGen(i)`` with ``args[i]``."""
    if isinstance(t, TGen):
        return args[t.index]
    if isinstance(t, TCon) and t.args:
        return TCon(t.name, tuple(substitute(a, args) for a in t.args))
    return t


def replace_constructors(t: Type, replacements: Mapping[str, Type]) -> Type:
    """Replace named type constructors with templates over their arguments."""
    t = prune(t)
    if isinstance(t, TCon):
        args = tuple(replace_constructors(a, replacements) for a in t.args)
        if t.name in replacements:
            return substitute(replacements[t.name], args)
        return TCon(t.name, args)
    return t


def instantiate(scheme: Scheme, level: int) -> Type:
    return instantiate_args(scheme, level)[0]


def instantiate_args(scheme: Scheme, level: int) -> tuple[Type, tuple[Type, ...]]:
    """Instantiate ``scheme`` with fresh variables, also returning them in
    ``TGen`` order (the explicit type application of the elaborated term)."""
    if scheme.arity == 0:
        return scheme.body, ()
    args = tuple(TVar(level) for _ in range(scheme.arity))
    return substitute(scheme.body, args), args


def arity_of(t: Type) -> int:
    """Number of arrows at the spine of ``t``."""
    n = 0
    t = prune(t)
    while isinstance(t, TCon) and t.name == ARROW:
        n += 1
        t = prune(t.args[1])
    return n


# ---------------------------------------------------------------- printing


class TypePrinter:
    """Prints types OCaml-style, naming variables 'a, 'b, ... consistently."""

    def __init__(self, type_names: dict[str, str] | None = None) -> None:
        self._names: dict[object, str] = {}
        self._type_names = type_names or {}

    def _var_name(self, key: object) -> str:
        if key not in self._names:
            n = len(self._names)
            letter = chr(ord("a") + n % 26)
            self._names[key] = f"'{letter}{n // 26 if n >= 26 else ''}"
        return self._names[key]

    def show(self, t: Type | Scheme) -> str:
        if isinstance(t, Scheme):
            t = t.body
        return self._show(t, 0)

    # precedence: 0 = arrow, 1 = tuple component, 2 = type argument
    def _show(self, t: Type, prec: int) -> str:
        t = prune(t)
        if isinstance(t, TVar):
            return self._var_name(("var", t.id))
        if isinstance(t, TGen):
            return self._var_name(("gen", t.index))
        assert isinstance(t, TCon)
        if t.name == ARROW:
            text = f"{self._show(t.args[0], 1)} -> {self._show(t.args[1], 0)}"
            return f"({text})" if prec > 0 else text
        if t.name == TUPLE:
            text = " * ".join(self._show(a, 2) for a in t.args)
            return f"({text})" if prec > 1 else text
        name = self._type_names.get(t.name, t.name.split("#", 1)[0])
        if not t.args:
            return name
        if len(t.args) == 1:
            return f"{self._show(t.args[0], 2)} {name}"
        return f"({', '.join(self._show(a, 0) for a in t.args)}) {name}"


def show(t: Type | Scheme) -> str:
    return TypePrinter().show(t)
