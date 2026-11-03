"""Core IR: the resolved, typed-checked functional kernel.

The type checker elaborates the surface AST into this IR. Compared to the
AST, every name is resolved (locals vs. fully qualified globals), syntactic
sugar is gone (``if``, lists, operators, multi-pattern parameters, pipes) and
constructors carry their runtime tag. The runtime only ever sees Core IR.

Type annotations. The checker also records the types it inferred, so that a
certificate checker can retype the program without inference (HYP-024): the
types of lambda parameters, the variables quantified at each ``let``, and the
explicit type arguments of every instantiation. Annotations are excluded from
equality and ignored by the interpreter. Inside an annotation, an unbound type
variable is always bound by an enclosing ``forall_vars`` (or ``foralls``); see
:mod:`hypomnesis.language.typesystem.annotations`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hypomnesis.language.errors import Span

if TYPE_CHECKING:
    from hypomnesis.language.typesystem.types import TVar, Type


# --------------------------------------------------------------- patterns


@dataclass(frozen=True)
class Pattern:
    pass


@dataclass(frozen=True)
class PWild(Pattern):
    pass


@dataclass(frozen=True)
class PVar(Pattern):
    name: str


@dataclass(frozen=True)
class PLit(Pattern):
    value: object


@dataclass(frozen=True)
class PCtor(Pattern):
    tag: str
    arg: Pattern | None


@dataclass(frozen=True)
class PTuple(Pattern):
    items: tuple[Pattern, ...]


@dataclass(frozen=True)
class PRecord(Pattern):
    fields: tuple[tuple[str, Pattern], ...]


@dataclass(frozen=True)
class POr(Pattern):
    left: Pattern
    right: Pattern


@dataclass(frozen=True)
class PAlias(Pattern):
    pattern: Pattern
    name: str


# ------------------------------------------------------------ expressions


@dataclass(frozen=True)
class Expr:
    pass


@dataclass(frozen=True)
class Literal(Expr):
    value: object


@dataclass(frozen=True)
class Local(Expr):
    name: str
    type_args: tuple[Type, ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class Global(Expr):
    qname: str
    type_args: tuple[Type, ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class Lambda(Expr):
    params: tuple[str, ...]
    body: Expr
    name: str = "<fun>"
    param_types: tuple[Type, ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class Apply(Expr):
    fn: Expr
    args: tuple[Expr, ...]


@dataclass(frozen=True)
class Let(Expr):
    name: str
    value: Expr
    body: Expr
    forall_vars: tuple[TVar, ...] = field(default=(), compare=False, repr=False)
    value_type: Type | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class LetRec(Expr):
    bindings: tuple[tuple[str, Lambda], ...]
    body: Expr
    types: tuple[Type, ...] = field(default=(), compare=False, repr=False)
    foralls: tuple[tuple[TVar, ...], ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class Case:
    pattern: Pattern
    guard: Expr | None
    body: Expr


@dataclass(frozen=True)
class Match(Expr):
    scrutinee: Expr
    cases: tuple[Case, ...]
    span: Span | None = field(default=None, compare=False)
    # Set when the match elaborates `let <pattern> = ...`: the pattern
    # variables are generalised over these type variables.
    forall_vars: tuple[TVar, ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class Tuple(Expr):
    items: tuple[Expr, ...]


@dataclass(frozen=True)
class Record(Expr):
    type_name: str
    fields: tuple[tuple[str, Expr], ...]
    type_args: tuple[Type, ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class RecordUpdate(Expr):
    base: Expr
    fields: tuple[tuple[str, Expr], ...]


@dataclass(frozen=True)
class Field(Expr):
    expr: Expr
    name: str


@dataclass(frozen=True)
class Construct(Expr):
    tag: str
    index: int
    arg: Expr | None
    type_args: tuple[Type, ...] = field(default=(), compare=False, repr=False)


# ------------------------------------------------------- top-level forms


@dataclass(frozen=True)
class Definition:
    pass


@dataclass(frozen=True)
class DefValue(Definition):
    """Evaluate ``expr``, match it against ``pattern`` and publish the
    pattern variables as globals: ``targets`` maps local name -> qname."""

    pattern: Pattern
    expr: Expr
    targets: tuple[tuple[str, str], ...]
    span: Span | None = field(default=None, compare=False)
    forall_vars: tuple[TVar, ...] = field(default=(), compare=False, repr=False)
    value_type: Type | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class DefRec(Definition):
    bindings: tuple[tuple[str, Lambda], ...]
    types: tuple[Type, ...] = field(default=(), compare=False, repr=False)
    foralls: tuple[tuple[TVar, ...], ...] = field(default=(), compare=False, repr=False)


@dataclass(frozen=True)
class DefNative(Definition):
    qname: str
    symbol: str
    arity: int
    forall_vars: tuple[TVar, ...] = field(default=(), compare=False, repr=False)
    value_type: Type | None = field(default=None, compare=False, repr=False)
