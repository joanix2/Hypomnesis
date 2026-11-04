"""High-level entry point: parse, type-check, elaborate and run programs.

A :class:`Session` owns a type environment and a runtime environment that
grow together; the prelude is loaded first, then each loaded source extends
the session (as in a REPL).
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from typing import TypeVar

from hypomnesis.ir import core as ir
from hypomnesis.language import ast as A
from hypomnesis.language.errors import EvaluationError
from hypomnesis.language.parser import parse_expression, parse_program
from hypomnesis.language.typesystem.infer import Checker, CheckResult, TypeInfo, ValueInfo
from hypomnesis.language.typesystem.types import TypePrinter
from hypomnesis.runtime.interpreter import Interpreter
from hypomnesis.runtime.natives import NativeRegistry, default_registry
from hypomnesis.runtime.values import Value, show

T = TypeVar("T")


@dataclass(frozen=True)
class Binding:
    """A top-level value produced by a loaded program."""

    name: str
    qname: str
    type: str
    value: Value

    @property
    def display_name(self) -> str:
        """Qualified source name (redefinitions carry an internal ``#n`` suffix)."""
        return self.qname.split("#", 1)[0]

    def render(self) -> str:
        return f"val {self.display_name} : {self.type} = {show(self.value)}"

    def render_signature(self) -> str:
        return f"val {self.display_name} : {self.type}"


@dataclass(frozen=True)
class LoadResult:
    bindings: list[Binding]
    types: list[TypeInfo]


@cache
def prelude_source() -> str:
    return files("hypomnesis.stdlib").joinpath("prelude.hyp").read_text()


class Session:
    def __init__(self, natives: NativeRegistry | None = None, *, prelude: bool = True) -> None:
        self.natives = natives or default_registry()
        self.checker = Checker(self.natives.arities())
        self.interpreter = Interpreter(self.natives)
        # Every elaborated definition, in order (the prelude included): the
        # content of a certificate (see hypomnesis.certify).
        self.definitions: list[ir.Definition] = []
        if prelude:
            self.load(prelude_source())
        self.prelude_definitions = len(self.definitions)

    def check(self, source: str) -> LoadResult:
        """Type-check ``source`` and extend the type environment, without running it."""
        return self.check_program(parse_program(source))

    def check_program(self, program: A.Program) -> LoadResult:
        """Check an already parsed program, retaining its original source positions."""
        result = self.checker.check_program(program)
        self.definitions.extend(result.definitions)
        return LoadResult([self._binding(info, None) for info in result.values], result.types)

    def load(self, source: str) -> LoadResult:
        """Type-check and run ``source``, extending the session."""
        return self.load_program(parse_program(source))

    def load_program(self, program: A.Program) -> LoadResult:
        """Check and evaluate an already parsed program."""
        return self._run(self.checker.check_program(program))

    def _run(self, result: CheckResult) -> LoadResult:
        self.definitions.extend(result.definitions)
        run_deep(lambda: self.interpreter.execute(result.definitions))
        bindings = [
            self._binding(info, self.interpreter.globals[info.qname]) for info in result.values
        ]
        return LoadResult(bindings, result.types)

    def eval(self, source: str) -> Binding:
        """Evaluate an expression and return it as the binding ``it``."""
        expr = parse_expression(source)
        item = A.LetItem(False, (A.FunBinding("it", (), None, expr, span=expr.span),))
        result = self._run(self.checker.check_program(A.Program((item,))))
        return result.bindings[-1]

    def value(self, path: str) -> Value:
        return self.interpreter.globals[self.checker.lookup_value(path).qname]

    def type_of(self, path: str) -> str:
        return TypePrinter().show(self.checker.lookup_value(path).scheme)

    @staticmethod
    def _binding(info: ValueInfo, value: Value) -> Binding:
        return Binding(info.name, info.qname, TypePrinter().show(info.scheme), value)


# ------------------------------------------------------------- deep stacks

_STACK_SIZE = 512 * 1024 * 1024
_RECURSION_LIMIT = 1_000_000
_local = threading.local()


def run_deep(fn: Callable[[], T]) -> T:
    """Run ``fn`` on a thread with a large stack so that deep (non-tail)
    recursion in interpreted programs does not overflow the C stack."""
    if getattr(_local, "deep", False):
        return fn()
    outcome: dict[str, object] = {}

    def target() -> None:
        _local.deep = True
        try:
            outcome["value"] = fn()
        except BaseException as exc:  # re-raised on the calling thread
            outcome["error"] = exc

    previous_limit = sys.getrecursionlimit()
    previous_size = threading.stack_size()
    sys.setrecursionlimit(max(previous_limit, _RECURSION_LIMIT))
    try:
        threading.stack_size(_STACK_SIZE)
        thread = threading.Thread(target=target, name="hypomnesis-eval")
        thread.start()
    finally:
        threading.stack_size(previous_size)
    thread.join()
    if "error" in outcome:
        error = outcome["error"]
        if isinstance(error, RecursionError):
            raise EvaluationError("Stack_overflow") from None
        raise error  # type: ignore[misc]
    return outcome["value"]  # type: ignore[return-value]
