"""Evaluator for the Core IR.

Each IR node is compiled once into a Python closure ``env -> value``.
Calls in tail position return a :class:`_TailCall` that the application loop
unwinds, so tail-recursive Hypomnesis functions run in constant stack.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from hypomnesis.ir import core as ir
from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.natives import NativeRegistry, default_registry
from hypomnesis.runtime.values import (
    Closure,
    Function,
    Native,
    Partial,
    RecordValue,
    Value,
    Variant,
)


class Env:
    __slots__ = ("parent", "vars")

    def __init__(self, vars: dict[str, Value], parent: Env | None) -> None:
        self.vars = vars
        self.parent = parent


class _TailCall:
    __slots__ = ("args", "fn")

    def __init__(self, fn: Value, args: list[Value]) -> None:
        self.fn = fn
        self.args = args


Code = Callable[[Env | None], Value]
Matcher = Callable[[Value, dict[str, Value]], bool]


class Interpreter:
    def __init__(self, natives: NativeRegistry | None = None) -> None:
        self.natives = natives or default_registry()
        self.globals: dict[str, Value] = {}

    # ------------------------------------------------------------ public

    def execute(self, definitions: Iterable[ir.Definition]) -> None:
        for definition in definitions:
            self._define(definition)

    def evaluate(self, expr: ir.Expr) -> Value:
        return self.compile(expr)(None)

    def apply(self, fn: Value, args: list[Value]) -> Value:
        while True:
            if not isinstance(fn, Function):
                raise EvaluationError("attempt to apply a non-function value")
            arity = fn.arity
            if len(args) < arity:
                return Partial(fn, tuple(args))
            if len(args) > arity:
                fn, args = self.apply(fn, args[:arity]), args[arity:]
                continue
            if isinstance(fn, Closure):
                result = fn.body(Env(dict(zip(fn.params, args, strict=True)), fn.env))
                if isinstance(result, _TailCall):
                    fn, args = result.fn, result.args
                    continue
                return result
            if isinstance(fn, Native):
                return fn.fn(*args)
            assert isinstance(fn, Partial)
            fn, args = fn.fn, [*fn.args, *args]

    # ------------------------------------------------------- definitions

    def _define(self, d: ir.Definition) -> None:
        if isinstance(d, ir.DefValue):
            value = self.evaluate(d.expr)
            binds: dict[str, Value] = {}
            if not self._matcher(d.pattern)(value, binds):
                raise EvaluationError("Match_failure", d.span)
            for local, qname in d.targets:
                self.globals[qname] = binds[local]
        elif isinstance(d, ir.DefRec):
            for qname, lam in d.bindings:
                body = self.compile(lam.body, tail=True)
                self.globals[qname] = Closure(lam.params, body, None, lam.name)
        elif isinstance(d, ir.DefNative):
            spec = self.natives.get(d.symbol)
            self.globals[d.qname] = (
                spec.fn() if d.arity == 0 else Native(d.symbol, d.arity, spec.fn)
            )
        else:  # pragma: no cover
            raise EvaluationError(f"unknown definition {type(d).__name__}")

    # ----------------------------------------------------------- compiler

    def compile(self, node: ir.Expr, tail: bool = False) -> Code:
        return getattr(self, f"_c_{type(node).__name__}")(node, tail)

    def _c_Literal(self, node: ir.Literal, tail: bool) -> Code:
        value = node.value
        return lambda env: value

    def _c_Local(self, node: ir.Local, tail: bool) -> Code:
        name = node.name

        def run(env: Env | None) -> Value:
            while env is not None:
                vars = env.vars
                if name in vars:
                    return vars[name]
                env = env.parent
            raise EvaluationError(f"unbound local {name}")

        return run

    def _c_Global(self, node: ir.Global, tail: bool) -> Code:
        table, qname = self.globals, node.qname
        return lambda env: table[qname]

    def _c_Lambda(self, node: ir.Lambda, tail: bool) -> Code:
        params, name = node.params, node.name
        body = self.compile(node.body, tail=True)
        return lambda env: Closure(params, body, env, name)

    def _c_Apply(self, node: ir.Apply, tail: bool) -> Code:
        fn = self.compile(node.fn)
        args = [self.compile(a) for a in node.args]
        if tail:
            return lambda env: _TailCall(fn(env), [a(env) for a in args])
        apply = self.apply
        return lambda env: apply(fn(env), [a(env) for a in args])

    def _c_Let(self, node: ir.Let, tail: bool) -> Code:
        name = node.name
        value = self.compile(node.value)
        body = self.compile(node.body, tail)
        return lambda env: body(Env({name: value(env)}, env))

    def _c_LetRec(self, node: ir.LetRec, tail: bool) -> Code:
        lambdas = [
            (name, lam.params, self.compile(lam.body, tail=True), lam.name)
            for name, lam in node.bindings
        ]
        body = self.compile(node.body, tail)

        def run(env: Env | None) -> Value:
            inner = Env({}, env)
            for name, params, code, label in lambdas:
                inner.vars[name] = Closure(params, code, inner, label)
            return body(inner)

        return run

    def _c_Match(self, node: ir.Match, tail: bool) -> Code:
        scrutinee = self.compile(node.scrutinee)
        cases = [
            (
                self._matcher(case.pattern),
                None if case.guard is None else self.compile(case.guard),
                self.compile(case.body, tail),
            )
            for case in node.cases
        ]
        span = node.span

        def run(env: Env | None) -> Value:
            value = scrutinee(env)
            for match, guard, body in cases:
                binds: dict[str, Value] = {}
                if match(value, binds):
                    inner = Env(binds, env) if binds else env
                    if guard is None or guard(inner):
                        return body(inner)
            raise EvaluationError("Match_failure", span)

        return run

    def _c_Tuple(self, node: ir.Tuple, tail: bool) -> Code:
        items = [self.compile(x) for x in node.items]
        return lambda env: tuple(item(env) for item in items)

    def _c_Record(self, node: ir.Record, tail: bool) -> Code:
        type_name = node.type_name
        fields = [(name, self.compile(x)) for name, x in node.fields]
        return lambda env: RecordValue(type_name, tuple((n, c(env)) for n, c in fields))

    def _c_RecordUpdate(self, node: ir.RecordUpdate, tail: bool) -> Code:
        base = self.compile(node.base)
        fields = [(name, self.compile(x)) for name, x in node.fields]
        return lambda env: base(env).update({n: c(env) for n, c in fields})

    def _c_Field(self, node: ir.Field, tail: bool) -> Code:
        expr, name = self.compile(node.expr), node.name
        return lambda env: expr(env).get(name)

    def _c_Construct(self, node: ir.Construct, tail: bool) -> Code:
        tag, index = node.tag, node.index
        if node.arg is None:
            constant = Variant(tag, None, index)
            return lambda env: constant
        arg = self.compile(node.arg)
        return lambda env: Variant(tag, arg(env), index)

    # ----------------------------------------------------------- patterns

    def _matcher(self, p: ir.Pattern) -> Matcher:
        if isinstance(p, ir.PWild):
            return lambda v, b: True
        if isinstance(p, ir.PVar):
            name = p.name

            def bind(v: Value, b: dict[str, Value]) -> bool:
                b[name] = v
                return True

            return bind
        if isinstance(p, ir.PLit):
            expected = p.value
            return lambda v, b: v == expected
        if isinstance(p, ir.PCtor):
            tag = p.tag
            if p.arg is None:
                return lambda v, b: v.tag == tag
            sub = self._matcher(p.arg)
            return lambda v, b: v.tag == tag and sub(v.arg, b)
        if isinstance(p, ir.PTuple):
            subs = [self._matcher(x) for x in p.items]
            return lambda v, b: all(m(x, b) for m, x in zip(subs, v, strict=True))
        if isinstance(p, ir.PRecord):
            fields = [(name, self._matcher(x)) for name, x in p.fields]
            return lambda v, b: all(m(v.get(name), b) for name, m in fields)
        if isinstance(p, ir.POr):
            sides = (self._matcher(p.left), self._matcher(p.right))

            def either(v: Value, b: dict[str, Value]) -> bool:
                for side in sides:
                    trial: dict[str, Value] = {}
                    if side(v, trial):
                        b.update(trial)
                        return True
                return False

            return either
        if isinstance(p, ir.PAlias):
            inner, name = self._matcher(p.pattern), p.name

            def alias(v: Value, b: dict[str, Value]) -> bool:
                if inner(v, b):
                    b[name] = v
                    return True
                return False

            return alias
        raise EvaluationError(f"unknown pattern {type(p).__name__}")  # pragma: no cover
