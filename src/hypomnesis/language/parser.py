"""Lark-based parser turning source text into the surface AST."""

from __future__ import annotations

import ast as pyast
from functools import cache
from importlib.resources import files

from lark import Lark, Token, Transformer, v_args
from lark.exceptions import (
    UnexpectedCharacters,
    UnexpectedEOF,
    UnexpectedInput,
    UnexpectedToken,
    VisitError,
)

from hypomnesis.language import ast as A
from hypomnesis.language.errors import ParseError, Span


@cache
def _parser() -> Lark:
    grammar = files("hypomnesis.language.grammar").joinpath("hypomnesis.lark").read_text()
    return Lark(
        grammar,
        parser="lalr",
        start=["start", "expr"],
        propagate_positions=True,
        maybe_placeholders=True,
    )


def parse_program(source: str) -> A.Program:
    """Parse a sequence of top-level items."""
    return _parse(source, "start")


def parse_expression(source: str) -> A.Expr:
    """Parse a single expression (used by the REPL and embedding hosts)."""
    return _parse(source, "expr")


def _parse(source: str, start: str):
    try:
        tree = _parser().parse(source, start=start)
    except UnexpectedInput as exc:
        raise _convert_error(exc) from None
    try:
        return _ToAst().transform(tree)
    except VisitError as exc:
        if isinstance(exc.orig_exc, ParseError):
            raise exc.orig_exc from None
        raise


def _convert_error(exc: UnexpectedInput) -> ParseError:
    line, column = getattr(exc, "line", 0) or 0, getattr(exc, "column", 0) or 0
    if isinstance(exc, UnexpectedToken):
        token = exc.token
        found = "end of input" if token.type == "$END" else repr(str(token))
        expected = sorted(exc.accepts or exc.expected)
        message = f"unexpected {found}"
        if expected:
            message += f"; expected one of: {', '.join(expected[:8])}"
    elif isinstance(exc, UnexpectedCharacters):
        message = f"unexpected character {exc.char!r}"
    elif isinstance(exc, UnexpectedEOF):
        message = "unexpected end of input"
    else:
        message = str(exc)
    span = Span(line, column, line, column + 1) if line else None
    return ParseError(message, span)


def _span(meta) -> Span | None:
    if getattr(meta, "empty", True):
        return None
    return Span(meta.line, meta.column, meta.end_line, meta.end_column)


def _not_token(children, *types: str) -> list:
    return [c for c in children if not (isinstance(c, Token) and c.type in types)]


@v_args(meta=True)
class _ToAst(Transformer):
    # -------------------------------------------------------------- items

    def start(self, meta, children):
        return A.Program(tuple(children), span=_span(meta))

    def let_item(self, meta, children):
        rec, *bindings = children
        return A.LetItem(rec is not None, tuple(bindings), span=_span(meta))

    def type_item(self, meta, children):
        return A.TypeItem(tuple(children), span=_span(meta))

    def module_item(self, meta, children):
        name, *items = children
        if "." in name:
            raise ParseError(f"module name {name!s} must not be qualified", _span(meta))
        return A.ModuleItem(str(name), tuple(items), span=_span(meta))

    def open_item(self, meta, children):
        return A.OpenItem(str(children[0]), span=_span(meta))

    def external_item(self, meta, children):
        name, type_, symbol = children
        return A.ExternalItem(name, type_, pyast.literal_eval(str(symbol)), span=_span(meta))

    def value_name(self, meta, children):
        return str(children[0])

    def operator(self, meta, children):
        return str(children[0])

    def fun_binding(self, meta, children):
        name, *params, annot, body = children
        return A.FunBinding(name, tuple(params), annot, body, span=_span(meta))

    def pat_binding(self, meta, children):
        pattern, body = children
        return A.PatBinding(pattern, body, span=_span(meta))

    def binding_pattern(self, meta, children):
        return children[0]

    # -------------------------------------------------------- expressions

    def let_expr(self, meta, children):
        rec, *bindings, body = children
        return A.Let(rec is not None, tuple(bindings), body, span=_span(meta))

    def lambda_expr(self, meta, children):
        *params, body = children
        return A.Lambda(tuple(params), body, span=_span(meta))

    def function_expr(self, meta, children):
        return A.Function(children[0], span=_span(meta))

    def if_expr(self, meta, children):
        return A.If(*children, span=_span(meta))

    def match_expr(self, meta, children):
        scrutinee, arms = children
        return A.Match(scrutinee, arms, span=_span(meta))

    def match_arms(self, meta, children):
        return tuple(_not_token(children, "BAR"))

    def arm(self, meta, children):
        return A.Arm(*children, span=_span(meta))

    def binop(self, meta, children):
        left, op, right = children
        return A.BinOp(str(op), left, right, span=_span(meta))

    def cons_expr(self, meta, children):
        head, _, tail = children
        return A.Cons(head, tail, span=_span(meta))

    def neg(self, meta, children):
        return A.Neg(children[1], is_float=False, span=_span(meta))

    def fneg(self, meta, children):
        return A.Neg(children[1], is_float=True, span=_span(meta))

    def apply(self, meta, children):
        return A.Apply(*children, span=_span(meta))

    def field(self, meta, children):
        return A.Field(*children, span=_span(meta))

    def int_lit(self, meta, children):
        return A.Literal(int(str(children[0]).replace("_", "")), "int", span=_span(meta))

    def float_lit(self, meta, children):
        return A.Literal(float(str(children[0]).replace("_", "")), "float", span=_span(meta))

    def string_lit(self, meta, children):
        return A.Literal(pyast.literal_eval(str(children[0])), "string", span=_span(meta))

    def true_lit(self, meta, children):
        return A.Literal(True, "bool", span=_span(meta))

    def false_lit(self, meta, children):
        return A.Literal(False, "bool", span=_span(meta))

    def unit_lit(self, meta, children):
        return A.Literal((), "unit", span=_span(meta))

    def var(self, meta, children):
        return A.Var(str(children[0]), span=_span(meta))

    def ctor(self, meta, children):
        return A.Ctor(str(children[0]), span=_span(meta))

    def op_var(self, meta, children):
        return A.Var(children[0], span=_span(meta))

    def annot(self, meta, children):
        return A.Annot(*children, span=_span(meta))

    def tuple(self, meta, children):
        return A.Tuple(tuple(children), span=_span(meta))

    def nil(self, meta, children):
        return A.ListLit((), span=_span(meta))

    def list_lit(self, meta, children):
        return A.ListLit(tuple(children), span=_span(meta))

    def record(self, meta, children):
        return A.Record(tuple(children), span=_span(meta))

    def record_update(self, meta, children):
        base, *fields = children
        return A.RecordUpdate(base, tuple(fields), span=_span(meta))

    def field_assign(self, meta, children):
        return (children[0], children[1])

    def field_name(self, meta, children):
        return str(children[0])

    # ----------------------------------------------------------- patterns

    def palias(self, meta, children):
        return A.PAlias(children[0], str(children[1]), span=_span(meta))

    def por(self, meta, children):
        left, _, right = children
        return A.POr(left, right, span=_span(meta))

    def pcons(self, meta, children):
        head, _, tail = children
        return A.PCons(head, tail, span=_span(meta))

    def pctor_arg(self, meta, children):
        return A.PCtor(str(children[0]), children[1], span=_span(meta))

    def pctor(self, meta, children):
        return A.PCtor(str(children[0]), span=_span(meta))

    def pwild(self, meta, children):
        return A.PWild(span=_span(meta))

    def pvar(self, meta, children):
        return A.PVar(str(children[0]), span=_span(meta))

    def pint(self, meta, children):
        return A.PLit(int(str(children[0]).replace("_", "")), "int", span=_span(meta))

    def pnegint(self, meta, children):
        return A.PLit(-int(str(children[1]).replace("_", "")), "int", span=_span(meta))

    def pfloat(self, meta, children):
        return A.PLit(float(str(children[0]).replace("_", "")), "float", span=_span(meta))

    def pnegfloat(self, meta, children):
        return A.PLit(-float(str(children[1]).replace("_", "")), "float", span=_span(meta))

    def pstring(self, meta, children):
        return A.PLit(pyast.literal_eval(str(children[0])), "string", span=_span(meta))

    def ptrue(self, meta, children):
        return A.PLit(True, "bool", span=_span(meta))

    def pfalse(self, meta, children):
        return A.PLit(False, "bool", span=_span(meta))

    def punit(self, meta, children):
        return A.PLit((), "unit", span=_span(meta))

    def ptuple(self, meta, children):
        return A.PTuple(tuple(children), span=_span(meta))

    def pannot(self, meta, children):
        return A.PAnnot(*children, span=_span(meta))

    def pnil(self, meta, children):
        return A.PList((), span=_span(meta))

    def plist(self, meta, children):
        return A.PList(tuple(children), span=_span(meta))

    def precord(self, meta, children):
        return A.PRecord(tuple(children), span=_span(meta))

    def field_pat(self, meta, children):
        name, pattern = children
        if pattern is None:  # punning: { width } binds `width`
            pattern = A.PVar(name.rsplit(".", 1)[-1], span=_span(meta))
        return (name, pattern)

    # -------------------------------------------------------------- types

    def tarrow(self, meta, children):
        return A.TEArrow(children[0], children[2], span=_span(meta))

    def ttuple(self, meta, children):
        return A.TETuple(tuple(_not_token(children, "STAR")), span=_span(meta))

    def tapp(self, meta, children):
        arg, name = children
        return A.TECon(name, (arg,), span=_span(meta))

    def tappn(self, meta, children):
        *args, name = children
        return A.TECon(name, tuple(args), span=_span(meta))

    def tvar(self, meta, children):
        return A.TEVar(str(children[0]), span=_span(meta))

    def tcon(self, meta, children):
        return A.TECon(children[0], span=_span(meta))

    def type_name(self, meta, children):
        return str(children[0])

    def type_def(self, meta, children):
        params, name, rhs = children
        return A.TypeDef(str(name), params or (), rhs, span=_span(meta))

    def type_params(self, meta, children):
        return tuple(str(c) for c in children)

    def alias_rhs(self, meta, children):
        return A.AliasRhs(children[0], span=_span(meta))

    def record_rhs(self, meta, children):
        return A.RecordRhs(tuple(children), span=_span(meta))

    def variant_rhs(self, meta, children):
        return A.VariantRhs(tuple(_not_token(children, "BAR")), span=_span(meta))

    def field_decl(self, meta, children):
        return (str(children[0]), children[1])

    def ctor_decl(self, meta, children):
        name, arg = children
        if "." in name:
            raise ParseError(f"constructor name {name!s} must not be qualified", _span(meta))
        return (str(name), arg)
