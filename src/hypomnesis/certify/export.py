"""Export of the annotated Core IR as a JSON certificate (``certificate/1.0.0``).

The certificate is what an independent checker (the verified Lean checker of
HYP-026) re-typechecks without inference. Format, validated by
``contracts/schemas/certificate-1.0.0.json``:

* **Types** are ``{"con": name, "args": [...]}`` (including ``->`` and ``*``)
  or ``{"var": name}``; in type declarations, parameters are ``{"param": i}``.
  Type variables are renamed ``a0, a1, ...`` per definition, in quantifier
  order.
* **Locals** use de Bruijn indices: binders push their variables left to
  right and index 0 is the most recent. Binders are ``lam`` parameters,
  ``let``, every member of a ``letrec`` (for the members and the body), and
  pattern variables.
* **Patterns** bind numbered slots, pushed in slot order; a leaf
  ``{"bind": k}`` names its slot, so both sides of an or-pattern and aliases
  refer to the same slot unambiguously. Slots are numbered by first
  occurrence, left to right.
* Inside a ``rec`` group, members refer to each other through ``global``
  with empty ``type_args``: the monomorphic recursive binder. The scope of
  type variables in a group is the union of its quantifiers.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from hypomnesis.ir import core as ir
from hypomnesis.language.typesystem.infer import TypeInfo
from hypomnesis.language.typesystem.types import TCon, TGen, TVar, Type, prune

CERTIFICATE_VERSION = "1.0.0"
CERTIFICATE_SCHEMA_ID = "https://schemas.example.org/hypomnesis/certificate/1.0.0"

Json = dict[str, object]


class CertificateError(Exception):
    """The IR cannot be exported (missing annotation, free type variable)."""


def export_certificate(
    types: Iterable[TypeInfo], definitions: Iterable[ir.Definition], program_start: int = 0
) -> Json:
    """``program_start`` is the index of the first definition of the program
    itself (the ones before it come from the prelude)."""
    return {
        "certificate_version": CERTIFICATE_VERSION,
        "program_start": program_start,
        "types": [_type_decl(info) for info in types if info.kind != "alias"],
        "definitions": [_Exporter().definition(d) for d in definitions],
    }


# ------------------------------------------------------------------- types


def _template(t: Type) -> Json:
    if isinstance(t, TGen):
        return {"param": t.index}
    if isinstance(t, TCon):
        return {"con": t.name, "args": [_template(a) for a in t.args]}
    raise CertificateError(f"unexpected term in a type declaration: {t!r}")


def _type_decl(info: TypeInfo) -> Json:
    return {
        "name": info.qname,
        "params": info.arity,
        "kind": info.kind,
        "constructors": [
            {"tag": c.name, "index": c.index, "arg": None if c.arg is None else _template(c.arg)}
            for c in info.ctors
        ],
        "fields": [{"name": f.name, "type": _template(f.type)} for f in info.fields],
    }


# ------------------------------------------------------------------- terms


class _Exporter:
    def __init__(self) -> None:
        self.type_names: dict[int, str] = {}

    # types ---------------------------------------------------------------

    def quantify(self, variables: Sequence[TVar]) -> list[str]:
        """Name the variables of a quantifier (each once, in order)."""
        names: list[str] = []
        for v in variables:
            if v.id not in self.type_names:
                self.type_names[v.id] = f"a{len(self.type_names)}"
            if self.type_names[v.id] not in names:
                names.append(self.type_names[v.id])
        return names

    def type(self, t: Type | None) -> Json:
        if t is None:
            raise CertificateError("missing type annotation")
        t = prune(t)
        if isinstance(t, TVar):
            if t.id not in self.type_names:
                raise CertificateError("free type variable in an annotation")
            return {"var": self.type_names[t.id]}
        if isinstance(t, TCon):
            return {"con": t.name, "args": [self.type(a) for a in t.args]}
        raise CertificateError(f"unexpected type term {t!r}")

    def types(self, ts: Iterable[Type]) -> list[Json]:
        return [self.type(t) for t in ts]

    # definitions ---------------------------------------------------------

    def definition(self, d: ir.Definition) -> Json:
        if isinstance(d, ir.DefValue):
            forall = self.quantify(d.forall_vars)
            pattern, slots = self.pattern(d.pattern)
            targets = [{"slot": slots.index(local), "name": qname} for local, qname in d.targets]
            return {
                "value": {
                    "forall": forall,
                    "type": self.type(d.value_type),
                    "pattern": pattern,
                    "targets": targets,
                    "expr": self.expr(d.expr, []),
                }
            }
        if isinstance(d, ir.DefRec):
            if len(d.types) != len(d.bindings):
                raise CertificateError("let rec without type annotations")
            forall = self.quantify([v for vs in d.foralls for v in vs])
            bindings = [
                {"name": qname, "type": self.type(t), "lam": self.expr(lam, [])}
                for (qname, lam), t in zip(d.bindings, d.types, strict=True)
            ]
            return {"rec": {"forall": forall, "bindings": bindings}}
        if isinstance(d, ir.DefNative):
            return {
                "native": {
                    "name": d.qname,
                    "symbol": d.symbol,
                    "arity": d.arity,
                    "forall": self.quantify(d.forall_vars),
                    "type": self.type(d.value_type),
                }
            }
        raise CertificateError(f"unknown definition {type(d).__name__}")

    # expressions ---------------------------------------------------------

    @staticmethod
    def index(name: str, ctx: list[str]) -> int:
        for i in range(len(ctx) - 1, -1, -1):
            if ctx[i] == name:
                return len(ctx) - 1 - i
        raise CertificateError(f"unbound local {name}")

    def expr(self, e: ir.Expr, ctx: list[str]) -> Json:
        if isinstance(e, ir.Literal):
            return {"lit": _literal(e.value)}
        if isinstance(e, ir.Local):
            return {
                "local": {"index": self.index(e.name, ctx), "type_args": self.types(e.type_args)}
            }
        if isinstance(e, ir.Global):
            return {"global": {"name": e.qname, "type_args": self.types(e.type_args)}}
        if isinstance(e, ir.Lambda):
            if len(e.param_types) != len(e.params):
                raise CertificateError(f"function {e.name} without parameter types")
            body = self.expr(e.body, [*ctx, *e.params])
            return {"lam": {"params": self.types(e.param_types), "body": body}}
        if isinstance(e, ir.Apply):
            args = [self.expr(a, ctx) for a in e.args]
            return {"app": {"fn": self.expr(e.fn, ctx), "args": args}}
        if isinstance(e, ir.Let):
            forall = self.quantify(e.forall_vars)
            return {
                "let": {
                    "forall": forall,
                    "value_type": self.type(e.value_type),
                    "value": self.expr(e.value, ctx),
                    "body": self.expr(e.body, [*ctx, e.name]),
                }
            }
        if isinstance(e, ir.LetRec):
            if len(e.types) != len(e.bindings):
                raise CertificateError("let rec without type annotations")
            forall = self.quantify([v for vs in e.foralls for v in vs])
            inner = [*ctx, *(name for name, _ in e.bindings)]
            bindings = [
                {"type": self.type(t), "lam": self.expr(lam, inner)}
                for (_, lam), t in zip(e.bindings, e.types, strict=True)
            ]
            return {
                "letrec": {"forall": forall, "bindings": bindings, "body": self.expr(e.body, inner)}
            }
        if isinstance(e, ir.Match):
            forall = self.quantify(e.forall_vars)
            cases = []
            for case in e.cases:
                pattern, slots = self.pattern(case.pattern)
                inner = [*ctx, *slots]
                cases.append(
                    {
                        "pattern": pattern,
                        "guard": None if case.guard is None else self.expr(case.guard, inner),
                        "body": self.expr(case.body, inner),
                    }
                )
            return {
                "match": {
                    "forall": forall,
                    "scrutinee": self.expr(e.scrutinee, ctx),
                    "cases": cases,
                }
            }
        if isinstance(e, ir.Tuple):
            return {"tuple": [self.expr(x, ctx) for x in e.items]}
        if isinstance(e, ir.Record):
            fields = [{"name": n, "value": self.expr(x, ctx)} for n, x in e.fields]
            return {
                "record": {
                    "type": e.type_name,
                    "type_args": self.types(e.type_args),
                    "fields": fields,
                }
            }
        if isinstance(e, ir.RecordUpdate):
            fields = [{"name": n, "value": self.expr(x, ctx)} for n, x in e.fields]
            return {"update": {"base": self.expr(e.base, ctx), "fields": fields}}
        if isinstance(e, ir.Field):
            return {"field": {"expr": self.expr(e.expr, ctx), "name": e.name}}
        if isinstance(e, ir.Construct):
            if e.owner is None:
                raise CertificateError(f"constructor {e.tag} without its type")
            return {
                "construct": {
                    "type": e.owner,
                    "tag": e.tag,
                    "index": e.index,
                    "type_args": self.types(e.type_args),
                    "arg": None if e.arg is None else self.expr(e.arg, ctx),
                }
            }
        raise CertificateError(f"unknown expression {type(e).__name__}")

    # patterns ------------------------------------------------------------

    def pattern(self, p: ir.Pattern) -> tuple[Json, list[str]]:
        """Export a pattern; return it with its slot names, in slot order."""
        slots: list[str] = []

        def slot(name: str) -> int:
            if name not in slots:
                slots.append(name)
            return slots.index(name)

        def go(p: ir.Pattern) -> Json:
            if isinstance(p, ir.PWild):
                return {"wild": {}}
            if isinstance(p, ir.PVar):
                return {"bind": slot(p.name)}
            if isinstance(p, ir.PLit):
                return {"lit": _literal(p.value)}
            if isinstance(p, ir.PCtor):
                if p.index < 0:
                    raise CertificateError(f"constructor pattern {p.tag} without its index")
                arg = None if p.arg is None else go(p.arg)
                return {"ctor": {"tag": p.tag, "index": p.index, "arg": arg}}
            if isinstance(p, ir.PTuple):
                return {"tuple": [go(x) for x in p.items]}
            if isinstance(p, ir.PRecord):
                return {"record": [{"name": n, "pattern": go(x)} for n, x in p.fields]}
            if isinstance(p, ir.POr):
                return {"or": [go(p.left), go(p.right)]}
            if isinstance(p, ir.PAlias):
                inner = go(p.pattern)
                return {"alias": {"pattern": inner, "bind": slot(p.name)}}
            raise CertificateError(f"unknown pattern {type(p).__name__}")

        return go(p), slots


def _literal(value: object) -> Json:
    if isinstance(value, bool):
        return {"kind": "bool", "value": value}
    if isinstance(value, int):
        return {"kind": "int", "value": value}
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CertificateError("non-finite float literal")
        return {"kind": "float", "value": value}
    if isinstance(value, str):
        return {"kind": "string", "value": value}
    if value == ():
        return {"kind": "unit", "value": None}
    raise CertificateError(f"unexpected literal {value!r}")
