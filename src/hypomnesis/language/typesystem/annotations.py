"""Type annotations of the elaborated Core IR.

The checker records inferred types on the IR (see :mod:`hypomnesis.ir.core`).
This module walks them, with the type variables bound by enclosing
quantifiers in scope:

* :func:`close` gives a type to variables left unconstrained by inference
  (for instance the element type of ``[]`` in ``let _ = []``). Any choice is
  sound since nothing constrains them; like OCaml we pick ``unit``.
* :func:`annotation_problems` checks the invariant a certificate checker
  relies on: annotations are present, and every type variable they contain
  is bound by an enclosing ``forall_vars``/``foralls``.

Within a ``let rec`` group the scope is the union of the group's quantified
variables: the members are typed together and refer to each other
monomorphically.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass

from hypomnesis.ir import core as ir
from hypomnesis.language.typesystem.types import UNIT, TCon, TVar, Type, prune

Scope = frozenset[int]


@dataclass(frozen=True)
class Annotation:
    type: Type
    scope: Scope
    where: str


def _ids(variables: Iterable[TVar]) -> Scope:
    return frozenset(v.id for v in variables)


def free_variables(t: Type) -> list[TVar]:
    found: list[TVar] = []

    def go(t: Type) -> None:
        t = prune(t)
        if isinstance(t, TVar):
            if all(v is not t for v in found):
                found.append(t)
        elif isinstance(t, TCon):
            for arg in t.args:
                go(arg)

    go(t)
    return found


# ------------------------------------------------------------------- walk


class _Walker:
    def __init__(self) -> None:
        self.annotations: list[Annotation] = []
        self.missing: list[str] = []
        self.quantified: set[int] = set()

    def note(self, types: Iterable[Type], scope: Scope, where: str) -> None:
        for t in types:
            self.annotations.append(Annotation(t, scope, where))

    def bind(self, variables: Iterable[TVar], scope: Scope) -> Scope:
        ids = _ids(variables)
        self.quantified |= ids
        return scope | ids

    def definition(self, d: ir.Definition) -> None:
        if isinstance(d, ir.DefValue):
            scope = self.bind(d.forall_vars, frozenset())
            self._value_type(d.value_type, scope, f"définition {_targets(d)}")
            self.expr(d.expr, scope)
        elif isinstance(d, ir.DefRec):
            names = ", ".join(q for q, _ in d.bindings)
            if len(d.types) != len(d.bindings) or len(d.foralls) != len(d.bindings):
                self.missing.append(f"let rec {names} : types non annotés")
            scope = self.bind((v for vs in d.foralls for v in vs), frozenset())
            self.note(d.types, scope, f"let rec {names}")
            for _, lam in d.bindings:
                self.expr(lam, scope)
        elif isinstance(d, ir.DefNative):
            scope = self.bind(d.forall_vars, frozenset())
            self._value_type(d.value_type, scope, f"external {d.qname}")

    def _value_type(self, t: Type | None, scope: Scope, where: str) -> None:
        if t is None:
            self.missing.append(f"{where} : type non annoté")
        else:
            self.note([t], scope, where)

    def expr(self, e: ir.Expr, scope: Scope) -> None:
        if isinstance(e, ir.Local | ir.Global):
            name = e.name if isinstance(e, ir.Local) else e.qname
            self.note(e.type_args, scope, f"instanciation de {name}")
        elif isinstance(e, ir.Lambda):
            if len(e.param_types) != len(e.params):
                self.missing.append(f"fonction {e.name} : paramètres non annotés")
            self.note(e.param_types, scope, f"paramètres de {e.name}")
            self.expr(e.body, scope)
        elif isinstance(e, ir.Apply):
            self.expr(e.fn, scope)
            for arg in e.args:
                self.expr(arg, scope)
        elif isinstance(e, ir.Let):
            inner = self.bind(e.forall_vars, scope)
            self._value_type(e.value_type, inner, f"let {e.name}")
            self.expr(e.value, inner)
            self.expr(e.body, scope)
        elif isinstance(e, ir.LetRec):
            names = ", ".join(n for n, _ in e.bindings)
            if len(e.types) != len(e.bindings) or len(e.foralls) != len(e.bindings):
                self.missing.append(f"let rec {names} : types non annotés")
            inner = self.bind((v for vs in e.foralls for v in vs), scope)
            self.note(e.types, inner, f"let rec {names}")
            for _, lam in e.bindings:
                self.expr(lam, inner)
            self.expr(e.body, scope)
        elif isinstance(e, ir.Match):
            self.expr(e.scrutinee, self.bind(e.forall_vars, scope))
            for case in e.cases:
                if case.guard is not None:
                    self.expr(case.guard, scope)
                self.expr(case.body, scope)
        elif isinstance(e, ir.Tuple):
            for item in e.items:
                self.expr(item, scope)
        elif isinstance(e, ir.Record):
            self.note(e.type_args, scope, f"record {e.type_name}")
            for _, value in e.fields:
                self.expr(value, scope)
        elif isinstance(e, ir.RecordUpdate):
            self.expr(e.base, scope)
            for _, value in e.fields:
                self.expr(value, scope)
        elif isinstance(e, ir.Field):
            self.expr(e.expr, scope)
        elif isinstance(e, ir.Construct):
            self.note(e.type_args, scope, f"constructeur {e.tag}")
            if e.arg is not None:
                self.expr(e.arg, scope)


def _targets(d: ir.DefValue) -> str:
    return ", ".join(q for _, q in d.targets) or "_"


def _walk(definitions: Iterable[ir.Definition]) -> Iterator[_Walker]:
    for d in definitions:
        walker = _Walker()
        walker.definition(d)
        yield walker


# ------------------------------------------------------------------ public


def close(definitions: Iterable[ir.Definition]) -> int:
    """Default unconstrained type variables to ``unit``; return how many.

    A variable quantified anywhere in the definition is never defaulted.
    """
    count = 0
    for walker in _walk(definitions):
        for annotation in walker.annotations:
            for tv in free_variables(annotation.type):
                if tv.id not in walker.quantified:
                    tv.ref = UNIT
                    count += 1
    return count


def annotation_problems(definitions: Iterable[ir.Definition]) -> list[str]:
    """Missing annotations, and type variables not bound by an enclosing quantifier."""
    problems: list[str] = []
    for walker in _walk(definitions):
        problems.extend(walker.missing)
        for annotation in walker.annotations:
            for tv in free_variables(annotation.type):
                if tv.id not in annotation.scope:
                    problems.append(f"{annotation.where} : variable de type libre")
    return problems
