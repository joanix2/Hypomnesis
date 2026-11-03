"""Core IR: the resolved, typed-checked functional kernel.

The type checker elaborates the surface AST into this IR. Compared to the
AST, every name is resolved (locals vs. fully qualified globals), syntactic
sugar is gone (``if``, lists, operators, multi-pattern parameters, pipes) and
constructors carry their runtime tag. The runtime only ever sees Core IR.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from hypomnesis.language.errors import Span

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


@dataclass(frozen=True)
class Global(Expr):
    qname: str


@dataclass(frozen=True)
class Lambda(Expr):
    params: tuple[str, ...]
    body: Expr
    name: str = "<fun>"


@dataclass(frozen=True)
class Apply(Expr):
    fn: Expr
    args: tuple[Expr, ...]


@dataclass(frozen=True)
class Let(Expr):
    name: str
    value: Expr
    body: Expr


@dataclass(frozen=True)
class LetRec(Expr):
    bindings: tuple[tuple[str, Lambda], ...]
    body: Expr


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


@dataclass(frozen=True)
class Tuple(Expr):
    items: tuple[Expr, ...]


@dataclass(frozen=True)
class Record(Expr):
    type_name: str
    fields: tuple[tuple[str, Expr], ...]


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


@dataclass(frozen=True)
class DefRec(Definition):
    bindings: tuple[tuple[str, Lambda], ...]


@dataclass(frozen=True)
class DefNative(Definition):
    qname: str
    symbol: str
    arity: int
