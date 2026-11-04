"""Import of a JSON certificate back into annotated Core IR.

The inverse of :mod:`hypomnesis.certify.export`, up to the names of locals
(regenerated as ``v1, v2, ...``) and source spans. It exists to test that the
export loses nothing: ``export(load(c)) == c``, and the loaded IR runs like
the original.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Sequence
from functools import cache
from typing import Any, cast

from hypomnesis.certify.export import CERTIFICATE_SCHEMA_ID, CertificateError, Json
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.ir import core as ir
from hypomnesis.language.typesystem.types import TCon, TVar, Type


def load_definitions(certificate: Json) -> list[ir.Definition]:
    """Validate the certificate against its schema, then rebuild the IR.

    The schema is the single description of the structure (ADR 0004): once it
    holds, the loader only deconstructs. What a schema cannot say (scopes,
    bound type variables, slot numbering) is checked while loading.
    """
    version = certificate.get("certificate_version")
    if version not in ("1.0.0", "1.1.0"):
        raise CertificateError(
            f"$.certificate_version: unsupported certificate version: {version!r}"
        )
    schema = CERTIFICATE_SCHEMA_ID.rsplit("/", 1)[0] + "/" + str(version)
    issues = _registry().issues(schema, certificate)
    if issues:
        raise CertificateError("invalid certificate: " + "; ".join(map(str, issues)))
    return [_Loader().definition(d) for d in cast(list[Any], certificate["definitions"])]


@cache
def _registry() -> SchemaRegistry:
    return SchemaRegistry.with_builtin_schemas()


# ------------------------------------------------------------ deconstruction
# The schema guarantees every shape below, so payloads are read as plain JSON.


def _single(x: Any) -> tuple[str, Any]:
    """The (kind, payload) of a one-key object such as ``{"lam": {...}}``."""
    ((kind, payload),) = x.items()
    return kind, payload


def _literal(lit: Any) -> object:
    kind, value = lit["kind"], lit["value"]
    if kind == "unit":
        return ()
    if kind == "float":
        if "bits" in lit:
            value = struct.unpack(">d", int(lit["bits"]).to_bytes(8, "big"))[0]
            if not math.isfinite(value) or struct.pack(">d", float(lit["value"])) != struct.pack(
                ">d", value
            ):
                raise CertificateError("float literal bits disagree with its finite value")
            return value
        return float(value)
    if kind == "int":
        return int(value)  # the schema accepts 1.0 as an integer
    return value


# ------------------------------------------------------------------ loader


class _Loader:
    def __init__(self) -> None:
        self.type_vars: dict[str, TVar] = {}
        self.counter = 0

    def fresh(self) -> str:
        self.counter += 1
        return f"v{self.counter}"

    # types ---------------------------------------------------------------

    def quantify(self, names: Sequence[str]) -> tuple[TVar, ...]:
        return tuple(self.type_vars.setdefault(n, TVar(1)) for n in names)

    def type(self, t: Any) -> Type:
        if "var" in t:
            name = t["var"]
            if name not in self.type_vars:
                raise CertificateError(f"unbound type variable {name}")
            return self.type_vars[name]
        if "con" in t:
            return TCon(t["con"], self.types(t["args"]))
        raise CertificateError(f"invalid type {t}")

    def types(self, xs: Any) -> tuple[Type, ...]:
        return tuple(self.type(x) for x in xs)

    def lam(self, x: Any, ctx: list[str]) -> ir.Lambda:
        expr = self.expr(x, ctx)
        if not isinstance(expr, ir.Lambda):
            raise CertificateError("recursive binding is not a function")
        return expr

    # definitions ---------------------------------------------------------

    def definition(self, d: Json) -> ir.Definition:
        kind, p = _single(d)
        if kind == "value":
            forall = self.quantify(p["forall"])
            value_type = self.type(p["type"])
            pattern, slots = self.pattern(p["pattern"])
            targets = []
            for t in p["targets"]:
                slot = t["slot"]
                if not 0 <= slot < len(slots):
                    raise CertificateError(f"target slot {slot} not bound by the pattern")
                targets.append((slots[slot], t["name"]))
            expr = self.expr(p["expr"], [])
            return ir.DefValue(
                pattern, expr, tuple(targets), forall_vars=forall, value_type=value_type
            )
        if kind == "rec":
            forall = self.quantify(p["forall"])
            raw = p["bindings"]
            bindings = tuple((b["name"], self.lam(b["lam"], [])) for b in raw)
            types = tuple(self.type(b["type"]) for b in raw)
            # The group's union of quantifiers is carried by its first member.
            foralls = (forall, *(() for _ in raw[1:]))
            return ir.DefRec(bindings, types=types, foralls=foralls)
        if kind == "native":
            return ir.DefNative(
                p["name"],
                p["symbol"],
                p["arity"],
                forall_vars=self.quantify(p["forall"]),
                value_type=self.type(p["type"]),
            )
        raise CertificateError(f"invalid definition {kind}")

    # expressions ---------------------------------------------------------

    def expr(self, x: Any, ctx: list[str]) -> ir.Expr:
        kind, p = _single(x)
        if kind == "lit":
            return ir.Literal(_literal(p))
        if kind == "tuple":
            return ir.Tuple(tuple(self.expr(item, ctx) for item in p))
        if kind == "local":
            index = p["index"]
            if not 0 <= index < len(ctx):
                raise CertificateError(f"de Bruijn index {index} out of scope")
            return ir.Local(ctx[-1 - index], type_args=self.types(p["type_args"]))
        if kind == "global":
            return ir.Global(p["name"], type_args=self.types(p["type_args"]))
        if kind == "lam":
            param_types = self.types(p["params"])
            params = tuple(self.fresh() for _ in param_types)
            body = self.expr(p["body"], [*ctx, *params])
            return ir.Lambda(params, body, param_types=param_types)
        if kind == "app":
            args = tuple(self.expr(a, ctx) for a in p["args"])
            return ir.Apply(self.expr(p["fn"], ctx), args)
        if kind == "let":
            forall = self.quantify(p["forall"])
            name = self.fresh()
            return ir.Let(
                name,
                self.expr(p["value"], ctx),
                self.expr(p["body"], [*ctx, name]),
                forall_vars=forall,
                value_type=self.type(p["value_type"]),
            )
        if kind == "letrec":
            forall = self.quantify(p["forall"])
            raw = p["bindings"]
            names = [self.fresh() for _ in raw]
            inner = [*ctx, *names]
            bindings = tuple(
                (name, self.lam(b["lam"], inner)) for name, b in zip(names, raw, strict=True)
            )
            types = tuple(self.type(b["type"]) for b in raw)
            foralls = (forall, *(() for _ in raw[1:]))
            body = self.expr(p["body"], inner)
            return ir.LetRec(bindings, body, types=types, foralls=foralls)
        if kind == "match":
            forall = self.quantify(p["forall"])
            scrutinee = self.expr(p["scrutinee"], ctx)
            cases = []
            for c in p["cases"]:
                pattern, slots = self.pattern(c["pattern"])
                inner = [*ctx, *slots]
                guard = None if c["guard"] is None else self.expr(c["guard"], inner)
                cases.append(ir.Case(pattern, guard, self.expr(c["body"], inner)))
            return ir.Match(scrutinee, tuple(cases), forall_vars=forall)
        if kind == "record":
            return ir.Record(
                p["type"], self.fields(p["fields"], ctx), type_args=self.types(p["type_args"])
            )
        if kind == "update":
            return ir.RecordUpdate(self.expr(p["base"], ctx), self.fields(p["fields"], ctx))
        if kind == "field":
            return ir.Field(self.expr(p["expr"], ctx), p["name"])
        if kind == "construct":
            arg = None if p["arg"] is None else self.expr(p["arg"], ctx)
            return ir.Construct(
                p["tag"],
                p["index"],
                arg,
                type_args=self.types(p["type_args"]),
                owner=p["type"],
            )
        raise CertificateError(f"invalid expression {kind}")

    def fields(self, xs: Any, ctx: list[str]) -> tuple[tuple[str, ir.Expr], ...]:
        return tuple((f["name"], self.expr(f["value"], ctx)) for f in xs)

    # patterns ------------------------------------------------------------

    def pattern(self, x: Any) -> tuple[ir.Pattern, list[str]]:
        """Load a pattern; return it with its slot names, in slot order."""
        names: dict[int, str] = {}

        def slot(index: int) -> str:
            if index not in names:
                names[index] = self.fresh()
            return names[index]

        def go(x: Any) -> ir.Pattern:
            kind, p = _single(x)
            if kind == "wild":
                return ir.PWild()
            if kind == "bind":
                return ir.PVar(slot(p))
            if kind == "lit":
                return ir.PLit(_literal(p))
            if kind == "tuple":
                return ir.PTuple(tuple(go(item) for item in p))
            if kind == "or":
                left, right = p
                return ir.POr(go(left), go(right))
            if kind == "record":
                return ir.PRecord(tuple((f["name"], go(f["pattern"])) for f in p))
            if kind == "ctor":
                arg = None if p["arg"] is None else go(p["arg"])
                return ir.PCtor(p["tag"], arg, index=p["index"])
            if kind == "alias":
                inner = go(p["pattern"])
                return ir.PAlias(inner, slot(p["bind"]))
            raise CertificateError(f"invalid pattern {kind}")

        pattern = go(x)
        if sorted(names) != list(range(len(names))):
            raise CertificateError("pattern slots are not numbered 0..n-1")
        return pattern, [names[i] for i in range(len(names))]
