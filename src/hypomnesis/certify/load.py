"""Import of a JSON certificate back into annotated Core IR.

The inverse of :mod:`hypomnesis.certify.export`, up to the names of locals
(regenerated as ``v1, v2, ...``) and source spans. It exists to test that the
export loses nothing: ``export(load(c)) == c``, and the loaded IR runs like
the original.
"""

from __future__ import annotations

from collections.abc import Sequence

from hypomnesis.certify.export import CertificateError, Json
from hypomnesis.ir import core as ir
from hypomnesis.language.typesystem.types import TCon, TVar, Type


def load_definitions(certificate: Json) -> list[ir.Definition]:
    return [_Loader().definition(_obj(d)) for d in _list(certificate.get("definitions"))]


# ------------------------------------------------------------- accessors


def _obj(x: object) -> Json:
    if not isinstance(x, dict):
        raise CertificateError(f"expected an object, got {type(x).__name__}")
    return x


def _list(x: object) -> list[object]:
    if not isinstance(x, list):
        raise CertificateError(f"expected a list, got {type(x).__name__}")
    return x


def _int(x: object) -> int:
    if not isinstance(x, int) or isinstance(x, bool):
        raise CertificateError(f"expected an integer, got {x!r}")
    return x


def _str(x: object) -> str:
    if not isinstance(x, str):
        raise CertificateError(f"expected a string, got {x!r}")
    return x


def _single(x: object) -> tuple[str, object]:
    """The (kind, payload) of a one-key object such as ``{"lam": {...}}``."""
    obj = _obj(x)
    if len(obj) != 1:
        raise CertificateError(f"expected a single-key object, got keys {sorted(obj)}")
    ((kind, payload),) = obj.items()
    return kind, payload


def _literal(x: object) -> object:
    lit = _obj(x)
    kind, value = lit.get("kind"), lit.get("value")
    if kind == "unit":
        return ()
    if kind == "float" and isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    if (kind, type(value)) in (("bool", bool), ("int", int), ("string", str)):
        return value
    raise CertificateError(f"invalid literal {lit}")


# ------------------------------------------------------------------ loader


class _Loader:
    def __init__(self) -> None:
        self.type_vars: dict[str, TVar] = {}
        self.counter = 0

    def fresh(self) -> str:
        self.counter += 1
        return f"v{self.counter}"

    # types ---------------------------------------------------------------

    def quantify(self, names: Sequence[object]) -> tuple[TVar, ...]:
        return tuple(self.type_vars.setdefault(_str(n), TVar(1)) for n in names)

    def type(self, x: object) -> Type:
        t = _obj(x)
        if "var" in t:
            name = _str(t["var"])
            if name not in self.type_vars:
                raise CertificateError(f"unbound type variable {name}")
            return self.type_vars[name]
        if "con" in t:
            return TCon(_str(t["con"]), self.types(t["args"]))
        raise CertificateError(f"invalid type {t}")

    def types(self, xs: object) -> tuple[Type, ...]:
        return tuple(self.type(x) for x in _list(xs))

    def lam(self, x: object, ctx: list[str]) -> ir.Lambda:
        expr = self.expr(x, ctx)
        if not isinstance(expr, ir.Lambda):
            raise CertificateError("recursive binding is not a function")
        return expr

    # definitions ---------------------------------------------------------

    def definition(self, d: Json) -> ir.Definition:
        kind, payload = _single(d)
        p = _obj(payload)
        if kind == "value":
            forall = self.quantify(_list(p["forall"]))
            value_type = self.type(p["type"])
            pattern, slots = self.pattern(p["pattern"])
            targets = []
            for t in map(_obj, _list(p["targets"])):
                slot = _int(t["slot"])
                if not 0 <= slot < len(slots):
                    raise CertificateError(f"target slot {slot} not bound by the pattern")
                targets.append((slots[slot], _str(t["name"])))
            expr = self.expr(p["expr"], [])
            return ir.DefValue(
                pattern, expr, tuple(targets), forall_vars=forall, value_type=value_type
            )
        if kind == "rec":
            forall = self.quantify(_list(p["forall"]))
            raw = [_obj(b) for b in _list(p["bindings"])]
            bindings = tuple((_str(b["name"]), self.lam(b["lam"], [])) for b in raw)
            types = tuple(self.type(b["type"]) for b in raw)
            # The group's union of quantifiers is carried by its first member.
            foralls = (forall, *(() for _ in raw[1:]))
            return ir.DefRec(bindings, types=types, foralls=foralls)
        if kind == "native":
            return ir.DefNative(
                _str(p["name"]),
                _str(p["symbol"]),
                _int(p["arity"]),
                forall_vars=self.quantify(_list(p["forall"])),
                value_type=self.type(p["type"]),
            )
        raise CertificateError(f"invalid definition {kind}")

    # expressions ---------------------------------------------------------

    def expr(self, x: object, ctx: list[str]) -> ir.Expr:
        kind, payload = _single(x)
        if kind == "lit":
            return ir.Literal(_literal(payload))
        if kind == "tuple":
            return ir.Tuple(tuple(self.expr(item, ctx) for item in _list(payload)))
        p = _obj(payload)
        if kind == "local":
            index = _int(p["index"])
            if not 0 <= index < len(ctx):
                raise CertificateError(f"de Bruijn index {index} out of scope")
            return ir.Local(ctx[-1 - index], type_args=self.types(p["type_args"]))
        if kind == "global":
            return ir.Global(_str(p["name"]), type_args=self.types(p["type_args"]))
        if kind == "lam":
            param_types = self.types(p["params"])
            params = tuple(self.fresh() for _ in param_types)
            body = self.expr(p["body"], [*ctx, *params])
            return ir.Lambda(params, body, param_types=param_types)
        if kind == "app":
            args = tuple(self.expr(a, ctx) for a in _list(p["args"]))
            return ir.Apply(self.expr(p["fn"], ctx), args)
        if kind == "let":
            forall = self.quantify(_list(p["forall"]))
            name = self.fresh()
            return ir.Let(
                name,
                self.expr(p["value"], ctx),
                self.expr(p["body"], [*ctx, name]),
                forall_vars=forall,
                value_type=self.type(p["value_type"]),
            )
        if kind == "letrec":
            forall = self.quantify(_list(p["forall"]))
            raw = [_obj(b) for b in _list(p["bindings"])]
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
            forall = self.quantify(_list(p["forall"]))
            scrutinee = self.expr(p["scrutinee"], ctx)
            cases = []
            for c in map(_obj, _list(p["cases"])):
                pattern, slots = self.pattern(c["pattern"])
                inner = [*ctx, *slots]
                guard = None if c["guard"] is None else self.expr(c["guard"], inner)
                cases.append(ir.Case(pattern, guard, self.expr(c["body"], inner)))
            return ir.Match(scrutinee, tuple(cases), forall_vars=forall)
        if kind == "record":
            return ir.Record(
                _str(p["type"]), self.fields(p["fields"], ctx), type_args=self.types(p["type_args"])
            )
        if kind == "update":
            return ir.RecordUpdate(self.expr(p["base"], ctx), self.fields(p["fields"], ctx))
        if kind == "field":
            return ir.Field(self.expr(p["expr"], ctx), _str(p["name"]))
        if kind == "construct":
            arg = None if p["arg"] is None else self.expr(p["arg"], ctx)
            return ir.Construct(
                _str(p["tag"]), _int(p["index"]), arg, type_args=self.types(p["type_args"])
            )
        raise CertificateError(f"invalid expression {kind}")

    def fields(self, xs: object, ctx: list[str]) -> tuple[tuple[str, ir.Expr], ...]:
        return tuple((_str(f["name"]), self.expr(f["value"], ctx)) for f in map(_obj, _list(xs)))

    # patterns ------------------------------------------------------------

    def pattern(self, x: object) -> tuple[ir.Pattern, list[str]]:
        """Load a pattern; return it with its slot names, in slot order."""
        names: dict[int, str] = {}

        def slot(k: object) -> str:
            index = _int(k)
            if index not in names:
                names[index] = self.fresh()
            return names[index]

        def go(x: object) -> ir.Pattern:
            kind, payload = _single(x)
            if kind == "wild":
                return ir.PWild()
            if kind == "bind":
                return ir.PVar(slot(payload))
            if kind == "lit":
                return ir.PLit(_literal(payload))
            if kind == "tuple":
                return ir.PTuple(tuple(go(item) for item in _list(payload)))
            if kind == "or":
                left, right = _list(payload)
                return ir.POr(go(left), go(right))
            if kind == "record":
                fields = tuple(
                    (_str(f["name"]), go(f["pattern"])) for f in map(_obj, _list(payload))
                )
                return ir.PRecord(fields)
            p = _obj(payload)
            if kind == "ctor":
                return ir.PCtor(_str(p["tag"]), None if p["arg"] is None else go(p["arg"]))
            if kind == "alias":
                inner = go(p["pattern"])
                return ir.PAlias(inner, slot(p["bind"]))
            raise CertificateError(f"invalid pattern {kind}")

        pattern = go(x)
        if sorted(names) != list(range(len(names))):
            raise CertificateError("pattern slots are not numbered 0..n-1")
        return pattern, [names[i] for i in range(len(names))]
