"""Name resolution, Hindley-Milner inference and elaboration to Core IR.

The :class:`Checker` is incremental: each call to :meth:`Checker.check_program`
extends the global environment (this is how the prelude, files and REPL
phrases are layered). A failed phrase leaves the environment untouched.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from hypomnesis.ir import core as ir
from hypomnesis.language import ast as A
from hypomnesis.language.errors import NameResolutionError, Span, TypeCheckError
from hypomnesis.language.typesystem.annotations import close
from hypomnesis.language.typesystem.types import (
    ARROW,
    BOOL,
    FLOAT,
    INT,
    STRING,
    UNIT,
    Scheme,
    TCon,
    TGen,
    TVar,
    Type,
    TypePrinter,
    arity_of,
    arrow,
    arrows,
    expect,
    generalize,
    generalize_vars,
    instantiate_args,
    list_of,
    mono,
    prune,
    substitute,
    tuple_of,
    unify,
)

LITERAL_TYPES: dict[str, Type] = {
    "int": INT,
    "float": FLOAT,
    "string": STRING,
    "bool": BOOL,
    "unit": UNIT,
}

Env = dict[str, Scheme]


# ------------------------------------------------------------ environment


@dataclass(eq=False)
class TypeInfo:
    qname: str
    name: str
    arity: int
    kind: str  # "builtin" | "alias" | "record" | "variant"
    alias: Type | None = None
    fields: list[FieldInfo] = field(default_factory=list)
    ctors: list[CtorInfo] = field(default_factory=list)

    def field(self, name: str) -> FieldInfo | None:
        return next((f for f in self.fields if f.name == name), None)


@dataclass(eq=False)
class CtorInfo:
    name: str
    owner: TypeInfo
    arg: Type | None  # template over the owner's parameters (TGen)
    index: int


@dataclass(eq=False)
class FieldInfo:
    name: str
    owner: TypeInfo
    type: Type  # template over the owner's parameters (TGen)
    index: int


@dataclass(eq=False)
class ValueInfo:
    name: str
    qname: str
    scheme: Scheme


@dataclass(eq=False)
class Namespace:
    path: str
    values: dict[str, ValueInfo] = field(default_factory=dict)
    types: dict[str, TypeInfo] = field(default_factory=dict)
    ctors: dict[str, CtorInfo] = field(default_factory=dict)
    fields: dict[str, FieldInfo] = field(default_factory=dict)
    modules: dict[str, Namespace] = field(default_factory=dict)

    def qualify(self, name: str) -> str:
        return f"{self.path}.{name}" if self.path else name

    def merge(self, other: Namespace) -> None:
        for kind in ("values", "types", "ctors", "fields", "modules"):
            getattr(self, kind).update(getattr(other, kind))


@dataclass(eq=False)
class Frame:
    """A module being defined: what it exports and what is visible inside."""

    exports: Namespace
    visible: Namespace


@dataclass
class CheckResult:
    definitions: list[ir.Definition]
    values: list[ValueInfo]
    types: list[TypeInfo]


@dataclass(frozen=True)
class _LetStep:
    """One binding of a local `let`: a name (``Let``) or a pattern (``Match``)."""

    name: str | None
    pattern: ir.Pattern | None
    value: ir.Expr
    value_type: Type
    forall_vars: tuple[TVar, ...]
    span: Span | None

    def bind(self, value: ir.Expr, body: ir.Expr) -> ir.Expr:
        if self.name is not None:
            return ir.Let(
                self.name, value, body, forall_vars=self.forall_vars, value_type=self.value_type
            )
        assert self.pattern is not None
        case = ir.Case(self.pattern, None, body)
        return ir.Match(value, (case,), self.span, forall_vars=self.forall_vars)


# ------------------------------------------------------------------ checker


class Checker:
    def __init__(self, natives: Mapping[str, int] | None = None) -> None:
        self.natives = dict(natives or {})
        self.root = Namespace("")
        self.frames = [Frame(self.root, Namespace(""))]
        self.used_qnames: set[str] = set()
        self._gensym_counter = 0
        self._annot_vars: dict[str, Type] = {}
        self._definitions: list[ir.Definition] = []
        self._new_values: list[ValueInfo] = []
        self._new_types: list[TypeInfo] = []
        self.types_by_qname: dict[str, TypeInfo] = {}
        self._install_builtins()

    def _install_builtins(self) -> None:
        for name in ("int", "float", "string", "bool", "unit"):
            self._define_type(TypeInfo(name, name, 0, "builtin"))
        self.list_info = TypeInfo("list", "list", 1, "builtin")
        self.nil = CtorInfo("[]", self.list_info, None, 0)
        self.cons = CtorInfo("::", self.list_info, tuple_of([TGen(0), list_of(TGen(0))]), 1)
        self.list_info.ctors = [self.nil, self.cons]
        self._define_type(self.list_info)
        self.used_qnames.update(
            {"type:" + n for n in ("int", "float", "string", "bool", "unit", "list")}
        )

    # ---------------------------------------------------------- public api

    def check_program(self, program: A.Program) -> CheckResult:
        """Check and elaborate ``program``, extending the environment.

        On error the environment is restored to its previous state.
        """
        saved = self._snapshot()
        self._definitions, self._new_values, self._new_types = [], [], []
        try:
            for item in program.items:
                self._annot_vars = {}
                self._check_item(item)
            close(self._definitions)
        except BaseException:
            self._restore(saved)
            raise
        return CheckResult(self._definitions, self._new_values, self._new_types)

    def lookup_value(self, path: str) -> ValueInfo:
        return self._lookup("values", path, None, "value")

    def lookup_type(self, path: str) -> TypeInfo:
        return self._lookup("types", path, None, "type")

    def resolve_type(self, source: str) -> Type:
        """Resolve a standalone signature without extending the inference environment."""
        from hypomnesis.language.parser import parse_type

        return self._to_type(parse_type(source), tvars={})

    def _snapshot(self):
        namespaces = (self.root, self.frames[0].visible)
        tables = [{k: copy.copy(v) for k, v in ns.__dict__.items()} for ns in namespaces]
        return namespaces, tables, set(self.used_qnames)

    def _restore(self, saved) -> None:
        namespaces, tables, used = saved
        del self.frames[1:]
        for ns, table in zip(namespaces, tables, strict=True):
            ns.__dict__.update(table)
        self.used_qnames = used

    # ------------------------------------------------------- name lookup

    @property
    def _frame(self) -> Frame:
        return self.frames[-1]

    def _fresh_qname(self, name: str, kind: str = "") -> str:
        base = self._frame.exports.qualify(name)
        qname, n = base, 0
        while kind + qname in self.used_qnames:
            n += 1
            qname = f"{base}#{n}"
        self.used_qnames.add(kind + qname)
        return qname

    def gensym(self) -> str:
        self._gensym_counter += 1
        return f"${self._gensym_counter}"

    def _lookup_module(self, path: str, span: Span | None) -> Namespace:
        first, *rest = path.split(".")
        module = None
        for frame in reversed(self.frames):
            if first in frame.visible.modules:
                module = frame.visible.modules[first]
                break
        if module is None:
            raise NameResolutionError(f"unbound module {first}", span)
        for segment in rest:
            if segment not in module.modules:
                raise NameResolutionError(f"unbound module {module.path}.{segment}", span)
            module = module.modules[segment]
        return module

    def _lookup(self, kind: str, path: str, span: Span | None, label: str):
        if path[0].isupper() and "." in path:  # operators such as `+.` are not paths
            module_path, name = path.rsplit(".", 1)
            table = getattr(self._lookup_module(module_path, span), kind)
            if name in table:
                return table[name]
        else:
            for frame in reversed(self.frames):
                table = getattr(frame.visible, kind)
                if path in table:
                    return table[path]
        raise NameResolutionError(f"unbound {label} {path}", span)

    def _define_value(self, name: str, qname: str, scheme: Scheme) -> ValueInfo:
        info = ValueInfo(name, qname, scheme)
        self._frame.exports.values[name] = info
        self._frame.visible.values[name] = info
        self._new_values.append(info)
        return info

    def _define_type(self, info: TypeInfo) -> None:
        self.types_by_qname[info.qname] = info
        self._frame.exports.types[info.name] = info
        self._frame.visible.types[info.name] = info

    # -------------------------------------------------------------- items

    def _check_item(self, item: A.Item) -> None:
        if isinstance(item, A.LetItem):
            self._check_let_item(item)
        elif isinstance(item, A.TypeItem):
            self._check_type_item(item)
        elif isinstance(item, A.ModuleItem):
            self._check_module(item)
        elif isinstance(item, A.OpenItem):
            module = self._lookup_module(item.path, item.span)
            self._frame.visible.merge(module)
        elif isinstance(item, A.ExternalItem):
            self._check_external(item)
        elif isinstance(item, A.LanguageItem):
            raise TypeCheckError(
                "language declarations require the package loader (check --langage or langage.hyp)",
                item.span,
            )
        else:  # pragma: no cover - parser never produces anything else
            raise TypeCheckError(f"unsupported item {type(item).__name__}", item.span)

    def _check_let_item(self, item: A.LetItem) -> None:
        if item.rec:
            self._check_let_rec_item(item)
            return
        pending: list[tuple[str, str, Scheme]] = []
        for binding in item.bindings:
            if isinstance(binding, A.FunBinding):
                t, value = self._infer_fun_binding(binding, {}, 1)
                pattern: ir.Pattern = ir.PVar(binding.name)
                binds = {binding.name: t}
            else:
                assert isinstance(binding, A.PatBinding)
                t, value = self.infer(binding.body, {}, 1)
                binds = {}
                pt, pattern = self._infer_pattern(binding.pattern, 1, binds)
                expect(pt, t, binding.pattern.span, "This pattern")
            targets = []
            for name, bt in binds.items():
                qname = self._fresh_qname(name)
                targets.append((name, qname))
                pending.append((name, qname, generalize(bt, 0)))
            _, quantified = generalize_vars(t, 0)
            self._definitions.append(
                ir.DefValue(
                    pattern,
                    value,
                    tuple(targets),
                    binding.span,
                    forall_vars=quantified,
                    value_type=t,
                )
            )
        for name, qname, scheme in pending:
            self._define_value(name, qname, scheme)

    def _check_let_rec_item(self, item: A.LetItem) -> None:
        bindings = self._rec_bindings(item.bindings)
        slots = []
        for binding in bindings:
            tv = TVar(1)
            qname = self._fresh_qname(binding.name)
            slots.append((binding, tv, self._define_value(binding.name, qname, mono(tv))))
        lambdas = []
        for binding, tv, info in slots:
            t, value = self._infer_fun_binding(binding, {}, 1)
            expect(t, tv, binding.span, f"The recursive definition of {binding.name}")
            assert isinstance(value, ir.Lambda)
            lambdas.append((info.qname, value))
        foralls = []
        for _, tv, info in slots:
            info.scheme, quantified = generalize_vars(tv, 0)
            foralls.append(quantified)
        types = tuple(tv for _, tv, _ in slots)
        self._definitions.append(ir.DefRec(tuple(lambdas), types=types, foralls=tuple(foralls)))

    def _rec_bindings(self, bindings: tuple[A.Binding, ...]) -> list[A.FunBinding]:
        result = []
        for binding in bindings:
            if not (
                isinstance(binding, A.FunBinding)
                and (binding.params or isinstance(binding.body, A.Lambda | A.Function))
            ):
                raise TypeCheckError(
                    "the right-hand side of `let rec` must be a function", binding.span
                )
            result.append(binding)
        return result

    def _check_type_item(self, item: A.TypeItem) -> None:
        pairs = []
        for d in item.defs:
            kind = {A.AliasRhs: "alias", A.RecordRhs: "record", A.VariantRhs: "variant"}[
                type(d.rhs)
            ]
            info = TypeInfo(self._fresh_qname(d.name, "type:"), d.name, len(d.params), kind)
            self._define_type(info)
            pairs.append((d, info))
        for d, info in pairs:
            if len(set(d.params)) != len(d.params):
                raise TypeCheckError(f"duplicate type parameter in {d.name}", d.span)
            params: dict[str, Type] = {p: TGen(i) for i, p in enumerate(d.params)}
            rhs = d.rhs
            if isinstance(rhs, A.AliasRhs):
                info.alias = self._to_type(rhs.type, params=params)
            elif isinstance(rhs, A.RecordRhs):
                for index, (name, te) in enumerate(rhs.fields):
                    if info.field(name):
                        raise TypeCheckError(f"field {name} is defined several times", d.span)
                    fi = FieldInfo(name, info, self._to_type(te, params=params), index)
                    info.fields.append(fi)
                    self._frame.exports.fields[name] = fi
                    self._frame.visible.fields[name] = fi
            else:
                for index, (name, te) in enumerate(rhs.ctors):
                    if any(c.name == name for c in info.ctors):
                        raise TypeCheckError(f"constructor {name} is defined several times", d.span)
                    arg = None if te is None else self._to_type(te, params=params)
                    ci = CtorInfo(name, info, arg, index)
                    info.ctors.append(ci)
                    self._frame.exports.ctors[name] = ci
                    self._frame.visible.ctors[name] = ci
            self._new_types.append(info)

    def _check_module(self, item: A.ModuleItem) -> None:
        namespace = Namespace(self._frame.exports.qualify(item.name))
        self.frames.append(Frame(namespace, Namespace(namespace.path)))
        try:
            for sub in item.items:
                self._check_item(sub)
        finally:
            self.frames.pop()
        self._frame.exports.modules[item.name] = namespace
        self._frame.visible.modules[item.name] = namespace

    def _check_external(self, item: A.ExternalItem) -> None:
        tvars: dict[str, Type] = {}
        t = self._to_type(item.type, tvars=tvars, level=1)
        if item.symbol not in self.natives:
            raise NameResolutionError(f"unknown native symbol {item.symbol!r}", item.span)
        arity = arity_of(t)
        if self.natives[item.symbol] != arity:
            raise TypeCheckError(
                f"native {item.symbol!r} takes {self.natives[item.symbol]} argument(s) "
                f"but its declared type has {arity}",
                item.span,
            )
        qname = self._fresh_qname(item.name)
        scheme, quantified = generalize_vars(t, 0)
        self._define_value(item.name, qname, scheme)
        self._definitions.append(
            ir.DefNative(qname, item.symbol, arity, forall_vars=quantified, value_type=t)
        )

    # ------------------------------------------------------- type syntax

    def _to_type(
        self,
        te: A.TypeExpr,
        *,
        params: dict[str, Type] | None = None,
        tvars: dict[str, Type] | None = None,
        level: int = 1,
    ) -> Type:
        def go(te: A.TypeExpr) -> Type:
            if isinstance(te, A.TEVar):
                if params is not None:
                    if te.name not in params:
                        raise TypeCheckError(f"unbound type parameter {te.name}", te.span)
                    return params[te.name]
                scope = self._annot_vars if tvars is None else tvars
                if te.name not in scope:
                    scope[te.name] = TVar(level)
                return scope[te.name]
            if isinstance(te, A.TEArrow):
                return arrow(go(te.param), go(te.result))
            if isinstance(te, A.TETuple):
                return tuple_of([go(t) for t in te.items])
            assert isinstance(te, A.TECon)
            info = self._lookup("types", te.path, te.span, "type constructor")
            if len(te.args) != info.arity:
                raise TypeCheckError(
                    f"type {te.path} expects {info.arity} argument(s) but is given {len(te.args)}",
                    te.span,
                )
            args = [go(a) for a in te.args]
            if info.kind == "alias":
                if info.alias is None:
                    raise TypeCheckError(f"recursive type abbreviation {te.path}", te.span)
                return substitute(info.alias, args)
            return TCon(info.qname, tuple(args))

        return go(te)

    # -------------------------------------------------------- expressions

    def infer(self, e: A.Expr, env: Env, level: int) -> tuple[Type, ir.Expr]:
        method = getattr(self, f"_infer_{type(e).__name__}")
        return method(e, env, level)

    def _infer_Literal(self, e: A.Literal, env: Env, level: int):
        return LITERAL_TYPES[e.kind], ir.Literal(e.value)

    def _infer_Var(self, e: A.Var, env: Env, level: int):
        if e.path in env:
            t, args = instantiate_args(env[e.path], level)
            return t, ir.Local(e.path, type_args=args)
        info = self._lookup("values", e.path, e.span, "value")
        t, args = instantiate_args(info.scheme, level)
        return t, ir.Global(info.qname, type_args=args)

    def _instantiate_ctor(self, info: CtorInfo, level: int) -> tuple[TCon, Type | None]:
        args = [TVar(level) for _ in range(info.owner.arity)]
        result = TCon(info.owner.qname, tuple(args))
        return result, None if info.arg is None else substitute(info.arg, args)

    def _infer_Ctor(self, e: A.Ctor, env: Env, level: int):
        info = self._lookup("ctors", e.path, e.span, "constructor")
        result, arg = self._instantiate_ctor(info, level)
        if arg is None:
            return result, ir.Construct(
                info.name, info.index, None, type_args=result.args, owner=info.owner.qname
            )
        name = self.gensym()
        body = ir.Construct(
            info.name, info.index, ir.Local(name), type_args=result.args, owner=info.owner.qname
        )
        lam = ir.Lambda((name,), body, name=info.name, param_types=(arg,))
        return arrow(arg, result), lam

    def _infer_Apply(self, e: A.Apply, env: Env, level: int):
        args: list[A.Expr] = []
        fn: A.Expr = e
        while isinstance(fn, A.Apply):
            args.append(fn.arg)
            fn = fn.fn
        args.reverse()
        if isinstance(fn, A.Ctor) and len(args) == 1:
            return self._construct(fn, args[0], env, level)
        ft, fn_ir = self.infer(fn, env, level)
        arg_irs = []
        for arg in args:
            pruned = prune(ft)
            if isinstance(pruned, TCon) and pruned.name == ARROW:
                param, result = pruned.args
            elif isinstance(pruned, TVar):
                param, result = TVar(level), TVar(level)
                unify(pruned, arrow(param, result))
            else:
                what = "is applied to too many arguments" if arg_irs else "is not a function"
                raise TypeCheckError(
                    f"this expression has type {TypePrinter().show(ft)}; it {what}", fn.span
                )
            at, arg_ir = self.infer(arg, env, level)
            expect(at, param, arg.span, "This argument")
            arg_irs.append(arg_ir)
            ft = result
        return ft, ir.Apply(fn_ir, tuple(arg_irs))

    def _construct(self, ctor: A.Ctor, arg: A.Expr, env: Env, level: int):
        info = self._lookup("ctors", ctor.path, ctor.span, "constructor")
        result, arg_t = self._instantiate_ctor(info, level)
        if arg_t is None:
            raise TypeCheckError(f"constructor {ctor.path} expects no argument", ctor.span)
        at, arg_ir = self.infer(arg, env, level)
        expect(at, arg_t, arg.span, "This argument")
        return result, ir.Construct(
            info.name, info.index, arg_ir, type_args=result.args, owner=info.owner.qname
        )

    def _params(self, patterns: tuple[A.Pattern, ...], env: Env, level: int, span: Span | None):
        """Elaborate parameter patterns into plain names plus wrapping matches."""
        binds: dict[str, Type] = {}
        types, names, matches = [], [], []
        for p in patterns:
            t, pattern = self._infer_pattern(p, level, binds)
            types.append(t)
            if isinstance(pattern, ir.PVar):
                names.append(pattern.name)
            elif isinstance(pattern, ir.PWild):
                names.append(self.gensym())
            else:
                name = self.gensym()
                names.append(name)
                matches.append((name, pattern))
        inner_env = {**env, **{k: mono(v) for k, v in binds.items()}}

        def wrap(body: ir.Expr) -> ir.Expr:
            for name, pattern in reversed(matches):
                body = ir.Match(ir.Local(name), (ir.Case(pattern, None, body),), span)
            return body

        return types, tuple(names), inner_env, wrap

    def _infer_Lambda(self, e: A.Lambda, env: Env, level: int):
        types, names, inner_env, wrap = self._params(e.params, env, level, e.span)
        bt, body = self.infer(e.body, inner_env, level)
        return arrows(types, bt), ir.Lambda(names, wrap(body), param_types=tuple(types))

    def _infer_Function(self, e: A.Function, env: Env, level: int):
        name = self.gensym()
        param = TVar(level)
        result, cases = self._infer_arms(param, e.arms, env, level)
        match = ir.Match(ir.Local(name), cases, e.span)
        return arrow(param, result), ir.Lambda((name,), match, param_types=(param,))

    def _infer_fun_binding(self, b: A.FunBinding, env: Env, level: int) -> tuple[Type, ir.Expr]:
        if b.params:
            types, names, inner_env, wrap = self._params(b.params, env, level, b.span)
        else:
            types, names, inner_env, wrap = [], (), env, None
        bt, body = self.infer(b.body, inner_env, level)
        if b.annot is not None:
            expect(bt, self._to_type(b.annot, level=level), b.body.span)
        if wrap is not None:
            lam = ir.Lambda(names, wrap(body), name=b.name, param_types=tuple(types))
            return arrows(types, bt), lam
        if isinstance(body, ir.Lambda):
            body = replace(body, name=b.name)
        return bt, body

    def _infer_Let(self, e: A.Let, env: Env, level: int):
        if e.rec:
            return self._infer_let_rec(e, env, level)
        new_env = dict(env)
        steps: list[_LetStep] = []
        for binding in e.bindings:
            if isinstance(binding, A.FunBinding):
                t, value = self._infer_fun_binding(binding, env, level + 1)
                scheme, quantified = generalize_vars(t, level)
                new_env[binding.name] = scheme
                steps.append(_LetStep(binding.name, None, value, t, quantified, binding.span))
            else:
                assert isinstance(binding, A.PatBinding)
                t, value = self.infer(binding.body, env, level + 1)
                binds: dict[str, Type] = {}
                pt, pattern = self._infer_pattern(binding.pattern, level + 1, binds)
                expect(pt, t, binding.pattern.span, "This pattern")
                for name, bt in binds.items():
                    new_env[name] = generalize(bt, level)
                _, quantified = generalize_vars(t, level)
                steps.append(_LetStep(None, pattern, value, t, quantified, binding.span))
        body_t, body = self.infer(e.body, new_env, level)

        # With `and`, every right-hand side sees the outer scope: evaluate
        # them into fresh temporaries before binding any user name. Each
        # temporary is generalised like its binding, then re-instantiated at
        # the identity (Λᾱ. temp [ᾱ]).
        if len(steps) > 1:
            temps = [self.gensym() for _ in steps]
            for temp, step in zip(reversed(temps), reversed(steps), strict=True):
                body = step.bind(ir.Local(temp, type_args=step.forall_vars), body)
            for temp, step in zip(reversed(temps), reversed(steps), strict=True):
                body = ir.Let(
                    temp,
                    step.value,
                    body,
                    forall_vars=step.forall_vars,
                    value_type=step.value_type,
                )
            return body_t, body
        return body_t, steps[0].bind(steps[0].value, body)

    def _infer_let_rec(self, e: A.Let, env: Env, level: int):
        bindings = self._rec_bindings(e.bindings)
        tvars = {b.name: TVar(level + 1) for b in bindings}
        rec_env = {**env, **{name: mono(tv) for name, tv in tvars.items()}}
        lambdas = []
        for b in bindings:
            t, value = self._infer_fun_binding(b, rec_env, level + 1)
            expect(t, tvars[b.name], b.span, f"The recursive definition of {b.name}")
            assert isinstance(value, ir.Lambda)
            lambdas.append((b.name, value))
        new_env = dict(env)
        foralls = []
        for name, tv in tvars.items():
            new_env[name], quantified = generalize_vars(tv, level)
            foralls.append(quantified)
        body_t, body = self.infer(e.body, new_env, level)
        types = tuple(tvars.values())
        return body_t, ir.LetRec(tuple(lambdas), body, types=types, foralls=tuple(foralls))

    def _infer_If(self, e: A.If, env: Env, level: int):
        ct, cond = self.infer(e.cond, env, level)
        expect(ct, BOOL, e.cond.span)
        tt, then = self.infer(e.then, env, level)
        et, orelse = self.infer(e.orelse, env, level)
        expect(et, tt, e.orelse.span)
        cases = (ir.Case(ir.PLit(True), None, then), ir.Case(ir.PWild(), None, orelse))
        return tt, ir.Match(cond, cases, e.span)

    def _infer_arms(self, scrutinee_t: Type, arms: tuple[A.Arm, ...], env: Env, level: int):
        result = TVar(level)
        cases = []
        for arm in arms:
            binds: dict[str, Type] = {}
            pt, pattern = self._infer_pattern(arm.pattern, level, binds)
            expect(pt, scrutinee_t, arm.pattern.span, "This pattern")
            arm_env = {**env, **{k: mono(v) for k, v in binds.items()}}
            guard = None
            if arm.guard is not None:
                gt, guard = self.infer(arm.guard, arm_env, level)
                expect(gt, BOOL, arm.guard.span, "This guard")
            bt, body = self.infer(arm.body, arm_env, level)
            expect(bt, result, arm.body.span)
            cases.append(ir.Case(pattern, guard, body))
        return result, tuple(cases)

    def _infer_Match(self, e: A.Match, env: Env, level: int):
        st, scrutinee = self.infer(e.scrutinee, env, level)
        result, cases = self._infer_arms(st, e.arms, env, level)
        return result, ir.Match(scrutinee, cases, e.span)

    def _infer_Tuple(self, e: A.Tuple, env: Env, level: int):
        pairs = [self.infer(item, env, level) for item in e.items]
        return tuple_of([t for t, _ in pairs]), ir.Tuple(tuple(x for _, x in pairs))

    def _infer_ListLit(self, e: A.ListLit, env: Env, level: int):
        item_t: Type = TVar(level)
        result: ir.Expr = ir.Construct("[]", 0, None, type_args=(item_t,), owner="list")
        items = []
        for item in e.items:
            t, x = self.infer(item, env, level)
            expect(t, item_t, item.span, "This list element")
            items.append(x)
        for x in reversed(items):
            result = ir.Construct("::", 1, ir.Tuple((x, result)), type_args=(item_t,), owner="list")
        return list_of(item_t), result

    def _infer_Cons(self, e: A.Cons, env: Env, level: int):
        ht, head = self.infer(e.head, env, level)
        tt, tail = self.infer(e.tail, env, level)
        expect(tt, list_of(ht), e.tail.span)
        return tt, ir.Construct("::", 1, ir.Tuple((head, tail)), type_args=(ht,), owner="list")

    def _record_owner(self, t: Type, name: str, span: Span | None) -> TypeInfo:
        """Find the record type owning field ``name``, preferring the known type of ``t``."""
        pruned = prune(t)
        if isinstance(pruned, TCon) and "." not in name:
            owner = self.types_by_qname.get(pruned.name)
            if owner is not None and owner.field(name):
                return owner
        return self._lookup("fields", name, span, "record field").owner

    def _check_fields(self, owner, args, fields, env, level, span):
        seen: dict[str, ir.Expr] = {}
        for name, expr in fields:
            short = name.rsplit(".", 1)[-1]
            fi = owner.field(short)
            if fi is None:
                raise TypeCheckError(f"field {short} does not belong to type {owner.name}", span)
            if short in seen:
                raise TypeCheckError(f"field {short} is defined several times", span)
            t, x = self.infer(expr, env, level)
            expect(t, substitute(fi.type, args), expr.span, f"The value of field {short}")
            seen[short] = x
        return seen

    def _infer_Record(self, e: A.Record, env: Env, level: int):
        owner = self._lookup("fields", e.fields[0][0], e.span, "record field").owner
        args = [TVar(level) for _ in range(owner.arity)]
        seen = self._check_fields(owner, args, e.fields, env, level, e.span)
        missing = [f.name for f in owner.fields if f.name not in seen]
        if missing:
            raise TypeCheckError(f"some record fields are undefined: {', '.join(missing)}", e.span)
        fields = tuple((f.name, seen[f.name]) for f in owner.fields)
        record = ir.Record(owner.qname, fields, type_args=tuple(args))
        return TCon(owner.qname, tuple(args)), record

    def _infer_RecordUpdate(self, e: A.RecordUpdate, env: Env, level: int):
        bt, base = self.infer(e.base, env, level)
        owner = self._record_owner(bt, e.fields[0][0], e.span)
        args = [TVar(level) for _ in range(owner.arity)]
        record_t = TCon(owner.qname, tuple(args))
        expect(bt, record_t, e.base.span)
        seen = self._check_fields(owner, args, e.fields, env, level, e.span)
        return record_t, ir.RecordUpdate(base, tuple(seen.items()))

    def _infer_Field(self, e: A.Field, env: Env, level: int):
        et, expr = self.infer(e.expr, env, level)
        owner = self._record_owner(et, e.name, e.span)
        short = e.name.rsplit(".", 1)[-1]
        fi = owner.field(short)
        assert fi is not None
        args = [TVar(level) for _ in range(owner.arity)]
        expect(et, TCon(owner.qname, tuple(args)), e.expr.span)
        return substitute(fi.type, args), ir.Field(expr, short)

    def _infer_Annot(self, e: A.Annot, env: Env, level: int):
        t, x = self.infer(e.expr, env, level)
        expect(t, self._to_type(e.type, level=level), e.expr.span)
        return t, x

    def _infer_BinOp(self, e: A.BinOp, env: Env, level: int):
        if e.op == "|>":
            return self.infer(A.Apply(e.right, e.left, span=e.span), env, level)
        if e.op == "@@":
            return self.infer(A.Apply(e.left, e.right, span=e.span), env, level)
        if e.op in ("&&", "||"):
            lt, left = self.infer(e.left, env, level)
            expect(lt, BOOL, e.left.span)
            rt, right = self.infer(e.right, env, level)
            expect(rt, BOOL, e.right.span)
            if e.op == "&&":
                cases = (
                    ir.Case(ir.PLit(True), None, right),
                    ir.Case(ir.PWild(), None, ir.Literal(False)),
                )
            else:
                cases = (
                    ir.Case(ir.PLit(True), None, ir.Literal(True)),
                    ir.Case(ir.PWild(), None, right),
                )
            return BOOL, ir.Match(left, cases, e.span)
        op = A.Var(e.op, span=e.span)
        return self.infer(
            A.Apply(A.Apply(op, e.left, span=e.span), e.right, span=e.span), env, level
        )

    def _infer_Neg(self, e: A.Neg, env: Env, level: int):
        kind = "float" if e.is_float else "int"
        if isinstance(e.expr, A.Literal) and e.expr.kind == kind:
            return LITERAL_TYPES[kind], ir.Literal(-e.expr.value)  # type: ignore[operator]
        zero = A.Literal(0.0 if e.is_float else 0, kind, span=e.span)
        return self.infer(
            A.BinOp("-." if e.is_float else "-", zero, e.expr, span=e.span), env, level
        )

    # ----------------------------------------------------------- patterns

    def _infer_pattern(
        self, p: A.Pattern, level: int, binds: dict[str, Type]
    ) -> tuple[Type, ir.Pattern]:
        if isinstance(p, A.PWild):
            return TVar(level), ir.PWild()
        if isinstance(p, A.PVar):
            return self._bind(p.name, TVar(level), binds, p.span), ir.PVar(p.name)
        if isinstance(p, A.PLit):
            return LITERAL_TYPES[p.kind], ir.PLit(p.value)
        if isinstance(p, A.PCtor):
            info = self._lookup("ctors", p.path, p.span, "constructor")
            return self._ctor_pattern(info, p.arg, p.path, level, binds, p.span)
        if isinstance(p, A.PTuple):
            pairs = [self._infer_pattern(item, level, binds) for item in p.items]
            return tuple_of([t for t, _ in pairs]), ir.PTuple(tuple(x for _, x in pairs))
        if isinstance(p, A.PList):
            item_t: Type = TVar(level)
            result: ir.Pattern = ir.PCtor("[]", None, index=0)
            subs = []
            for item in p.items:
                t, x = self._infer_pattern(item, level, binds)
                expect(t, item_t, item.span, "This pattern")
                subs.append(x)
            for x in reversed(subs):
                result = ir.PCtor("::", ir.PTuple((x, result)), index=1)
            return list_of(item_t), result
        if isinstance(p, A.PCons):
            ht, head = self._infer_pattern(p.head, level, binds)
            tt, tail = self._infer_pattern(p.tail, level, binds)
            expect(tt, list_of(ht), p.tail.span, "This pattern")
            return tt, ir.PCtor("::", ir.PTuple((head, tail)), index=1)
        if isinstance(p, A.PRecord):
            owner = self._lookup("fields", p.fields[0][0], p.span, "record field").owner
            args = [TVar(level) for _ in range(owner.arity)]
            fields = []
            for name, sub in p.fields:
                short = name.rsplit(".", 1)[-1]
                fi = owner.field(short)
                if fi is None:
                    raise TypeCheckError(
                        f"field {short} does not belong to type {owner.name}", p.span
                    )
                t, x = self._infer_pattern(sub, level, binds)
                expect(t, substitute(fi.type, args), sub.span, "This pattern")
                fields.append((short, x))
            return TCon(owner.qname, tuple(args)), ir.PRecord(tuple(fields))
        if isinstance(p, A.POr):
            left_binds: dict[str, Type] = {}
            right_binds: dict[str, Type] = {}
            lt, left = self._infer_pattern(p.left, level, left_binds)
            rt, right = self._infer_pattern(p.right, level, right_binds)
            expect(rt, lt, p.right.span, "This pattern")
            if left_binds.keys() != right_binds.keys():
                missing = sorted(left_binds.keys() ^ right_binds.keys())
                raise TypeCheckError(
                    f"variable {missing[0]} must occur on both sides of this | pattern", p.span
                )
            for name, bt in left_binds.items():
                expect(right_binds[name], bt, p.span, f"Variable {name}")
                self._bind(name, bt, binds, p.span)
            return lt, ir.POr(left, right)
        if isinstance(p, A.PAlias):
            t, x = self._infer_pattern(p.pattern, level, binds)
            self._bind(p.name, t, binds, p.span)
            return t, ir.PAlias(x, p.name)
        if isinstance(p, A.PAnnot):
            t, x = self._infer_pattern(p.pattern, level, binds)
            expect(t, self._to_type(p.type, level=level), p.span, "This pattern")
            return t, x
        raise TypeCheckError(f"unsupported pattern {type(p).__name__}", p.span)  # pragma: no cover

    def _ctor_pattern(self, info, arg, path, level, binds, span):
        result, arg_t = self._instantiate_ctor(info, level)
        if arg is None:
            if arg_t is not None:
                raise TypeCheckError(f"constructor {path} expects an argument", span)
            return result, ir.PCtor(info.name, None, index=info.index)
        if arg_t is None:
            raise TypeCheckError(f"constructor {path} expects no argument", span)
        t, x = self._infer_pattern(arg, level, binds)
        expect(t, arg_t, arg.span, "This pattern")
        return result, ir.PCtor(info.name, x, index=info.index)

    @staticmethod
    def _bind(name: str, t: Type, binds: dict[str, Type], span: Span | None) -> Type:
        if name in binds:
            raise TypeCheckError(f"variable {name} is bound several times in this pattern", span)
        binds[name] = t
        return t


def show_value_signature(info: ValueInfo) -> str:
    return f"val {info.name} : {TypePrinter().show(info.scheme)}"
