"""Surface syntax tree produced by the parser.

The AST mirrors the source closely; names are still unresolved strings
(possibly qualified, e.g. ``"Length.multiply"``). Name resolution and type
inference happen in :mod:`hypomnesis.language.typesystem`, which elaborates
this tree into the Core IR.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal as Lit
from typing import TypeAlias

from hypomnesis.language.errors import Span

LiteralKind = Lit["int", "float", "string", "bool", "unit"]


@dataclass(frozen=True)
class Node:
    span: Span | None = field(default=None, kw_only=True, compare=False, repr=False)


# ------------------------------------------------------------------ types


@dataclass(frozen=True)
class TypeExpr(Node):
    pass


@dataclass(frozen=True)
class TEVar(TypeExpr):
    name: str


@dataclass(frozen=True)
class TECon(TypeExpr):
    path: str
    args: tuple[TypeExpr, ...] = ()


@dataclass(frozen=True)
class TEArrow(TypeExpr):
    param: TypeExpr
    result: TypeExpr


@dataclass(frozen=True)
class TETuple(TypeExpr):
    items: tuple[TypeExpr, ...]


# --------------------------------------------------------------- patterns


@dataclass(frozen=True)
class Pattern(Node):
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
    kind: LiteralKind


@dataclass(frozen=True)
class PCtor(Pattern):
    path: str
    arg: Pattern | None = None


@dataclass(frozen=True)
class PTuple(Pattern):
    items: tuple[Pattern, ...]


@dataclass(frozen=True)
class PList(Pattern):
    items: tuple[Pattern, ...]


@dataclass(frozen=True)
class PCons(Pattern):
    head: Pattern
    tail: Pattern


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


@dataclass(frozen=True)
class PAnnot(Pattern):
    pattern: Pattern
    type: TypeExpr


# ------------------------------------------------------------ expressions


@dataclass(frozen=True)
class Expr(Node):
    pass


@dataclass(frozen=True)
class Literal(Expr):
    value: object
    kind: LiteralKind


@dataclass(frozen=True)
class Var(Expr):
    path: str


@dataclass(frozen=True)
class Ctor(Expr):
    path: str


@dataclass(frozen=True)
class Apply(Expr):
    fn: Expr
    arg: Expr


@dataclass(frozen=True)
class Lambda(Expr):
    params: tuple[Pattern, ...]
    body: Expr


@dataclass(frozen=True)
class Arm(Node):
    pattern: Pattern
    guard: Expr | None
    body: Expr


@dataclass(frozen=True)
class Function(Expr):
    arms: tuple[Arm, ...]


@dataclass(frozen=True)
class Binding(Node):
    pass


@dataclass(frozen=True)
class FunBinding(Binding):
    """``let name p1 ... pn [: t] = body``; ``n`` may be zero."""

    name: str
    params: tuple[Pattern, ...]
    annot: TypeExpr | None
    body: Expr


@dataclass(frozen=True)
class PatBinding(Binding):
    pattern: Pattern
    body: Expr


@dataclass(frozen=True)
class Let(Expr):
    rec: bool
    bindings: tuple[Binding, ...]
    body: Expr


@dataclass(frozen=True)
class If(Expr):
    cond: Expr
    then: Expr
    orelse: Expr


@dataclass(frozen=True)
class Match(Expr):
    scrutinee: Expr
    arms: tuple[Arm, ...]


@dataclass(frozen=True)
class Tuple(Expr):
    items: tuple[Expr, ...]


@dataclass(frozen=True)
class ListLit(Expr):
    items: tuple[Expr, ...]


@dataclass(frozen=True)
class Cons(Expr):
    head: Expr
    tail: Expr


@dataclass(frozen=True)
class Record(Expr):
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
class Annot(Expr):
    expr: Expr
    type: TypeExpr


@dataclass(frozen=True)
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Neg(Expr):
    expr: Expr
    is_float: bool


# ------------------------------------------------------------------ items


@dataclass(frozen=True)
class Item(Node):
    pass


ConfigValue: TypeAlias = str | int | bool | list["ConfigValue"] | dict[str, "ConfigValue"]


@dataclass(frozen=True)
class LanguageItem(Item):
    name: str
    configuration: dict[str, ConfigValue]


@dataclass(frozen=True)
class LetItem(Item):
    rec: bool
    bindings: tuple[Binding, ...]


@dataclass(frozen=True)
class AliasRhs(Node):
    type: TypeExpr


@dataclass(frozen=True)
class RecordRhs(Node):
    fields: tuple[tuple[str, TypeExpr], ...]


@dataclass(frozen=True)
class VariantRhs(Node):
    ctors: tuple[tuple[str, TypeExpr | None], ...]


TypeRhs = AliasRhs | RecordRhs | VariantRhs


@dataclass(frozen=True)
class TypeDef(Node):
    name: str
    params: tuple[str, ...]
    rhs: TypeRhs


@dataclass(frozen=True)
class TypeItem(Item):
    defs: tuple[TypeDef, ...]


@dataclass(frozen=True)
class ModuleItem(Item):
    name: str
    items: tuple[Item, ...]


@dataclass(frozen=True)
class OpenItem(Item):
    path: str


@dataclass(frozen=True)
class ExternalItem(Item):
    name: str
    type: TypeExpr
    symbol: str


@dataclass(frozen=True)
class Program(Node):
    items: tuple[Item, ...]
