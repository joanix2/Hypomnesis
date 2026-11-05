"""High-level entry point: parse, type-check, elaborate and run programs.

A :class:`Session` owns a type environment and a runtime environment that
grow together; the prelude is loaded first, then each loaded source extends
the session (as in a REPL).
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass, field
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import TypeVar

from hypomnesis.ir import core as ir
from hypomnesis.language import ast as A
from hypomnesis.language.errors import (
    CompilerWarning,
    EvaluationError,
    HypomnesisError,
    NameResolutionError,
)
from hypomnesis.language.parser import parse_expression, parse_program
from hypomnesis.language.typesystem.infer import (
    Checker,
    CheckResult,
    Namespace,
    TypeInfo,
    ValueInfo,
)
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
    warnings: list[CompilerWarning] = field(default_factory=list)


@dataclass(frozen=True)
class ImportedSource:
    path: Path
    text: str
    program: A.Program
    namespace: Namespace
    definitions: tuple[ir.Definition, ...]


@cache
def prelude_source() -> str:
    return files("hypomnesis.stdlib").joinpath("prelude.hyp").read_text()


class Session:
    def __init__(
        self,
        natives: NativeRegistry | None = None,
        *,
        prelude: bool = True,
        execute_prelude: bool = True,
    ) -> None:
        self.natives = natives or default_registry()
        self.checker = Checker(self.natives.arities())
        self.interpreter = Interpreter(self.natives)
        # Every elaborated definition, in order (the prelude included): the
        # content of a certificate (see hypomnesis.certify).
        self.definitions: list[ir.Definition] = []
        self.warnings: list[CompilerWarning] = []
        self.imported_sources: dict[Path, ImportedSource] = {}
        self._source_stack: list[Path] = []
        self._overlays: dict[str, str] = {}
        self._import_root: Path | None = None
        self._execute_imports = False
        self._executed_definitions: set[int] = set()
        self._failed_imports: set[Path] = set()
        self.checker.import_loader = self._load_import
        if prelude:
            if execute_prelude:
                self.load(prelude_source())
            else:
                self.check(prelude_source())
        self.prelude_definitions = len(self.definitions)
        self._import_prelude = copy(self.checker.root)
        for key in ("values", "types", "ctors", "fields", "modules"):
            setattr(self._import_prelude, key, dict(getattr(self.checker.root, key)))

    def check(self, source: str, *, filename: str | None = None) -> LoadResult:
        """Type-check ``source`` and extend the type environment, without running it."""
        return self.check_program(parse_program(source), filename=filename, source_text=source)

    def check_program(
        self,
        program: A.Program,
        *,
        filename: str | None = None,
        overlays: dict[str, str] | None = None,
        import_root: Path | None = None,
        source_text: str | None = None,
    ) -> LoadResult:
        """Check an already parsed program, retaining its original source positions."""
        result = self._compile(program, filename, overlays, import_root, source_text, execute=False)
        self._warnings(result, filename)
        self._remember_definitions(result.definitions)
        return LoadResult(
            [self._binding(info, None) for info in result.values], result.types, result.warnings
        )

    def load(self, source: str, *, filename: str | None = None) -> LoadResult:
        """Type-check and run ``source``, extending the session."""
        return self.load_program(parse_program(source), filename=filename, source_text=source)

    def load_program(
        self,
        program: A.Program,
        *,
        filename: str | None = None,
        import_root: Path | None = None,
        source_text: str | None = None,
    ) -> LoadResult:
        """Check and evaluate an already parsed program."""
        return self._run(
            self._compile(program, filename, None, import_root, source_text, execute=True), filename
        )

    def _compile(
        self,
        program: A.Program,
        filename: str | None,
        overlays: dict[str, str] | None,
        import_root: Path | None,
        source_text: str | None,
        *,
        execute: bool,
    ) -> CheckResult:
        self._source_stack = [Path(filename).resolve()] if filename else []
        self._overlays = {
            str(Path(path).resolve()): source for path, source in (overlays or {}).items()
        }
        self._import_root = import_root.resolve() if import_root else None
        self._execute_imports = execute
        saved = dict(self.imported_sources)
        before = {
            kind: dict(getattr(self.checker.root, kind))
            for kind in ("values", "types", "ctors", "fields", "modules")
        }
        try:
            result = self.checker.check_program(program)
            if filename:
                path = Path(filename).resolve()
                namespace = Namespace(str(path))
                for kind, members in before.items():
                    getattr(namespace, kind).update(
                        (name, value)
                        for name, value in getattr(self.checker.root, kind).items()
                        if members.get(name) is not value
                    )
                for item in program.items:
                    if isinstance(item, A.ImportItem):
                        name = (item.alias or item.member or item.path).split(".", 1)[0]
                        for kind in before:
                            if name in getattr(self.checker.root, kind):
                                getattr(namespace, kind)[name] = getattr(self.checker.root, kind)[
                                    name
                                ]
                self.imported_sources[path] = ImportedSource(
                    path, source_text or "", program, namespace, tuple(result.definitions)
                )
            return result
        except HypomnesisError:
            self.imported_sources = saved
            raise
        finally:
            self._source_stack = []

    def _load_import(self, item: A.ImportItem) -> Namespace:
        from hypomnesis.engine.errors import SourceError

        if not self._source_stack:
            raise NameResolutionError("file imports require a source filename", item.span)
        path = (
            self._source_stack[-1].parent / Path(*item.path.split(".")).with_suffix(".hyp")
        ).resolve()
        if self._import_root is not None and not path.is_relative_to(self._import_root):
            raise NameResolutionError(f"import outside language package: {path}", item.span)
        if path in self._source_stack:
            chain = " -> ".join(map(str, (*self._source_stack, path)))
            raise NameResolutionError(f"circular import: {chain}", item.span)
        if path in self._failed_imports:
            raise NameResolutionError(
                f"previous evaluation involving {path} failed; use a new session", item.span
            )
        if path in self.imported_sources:
            imported = self.imported_sources[path]
            if self._execute_imports:
                scheduled = {id(d) for d in self.checker._definitions}
                self.checker._definitions.extend(
                    d
                    for d in imported.definitions
                    if id(d) not in self._executed_definitions and id(d) not in scheduled
                )
            return imported.namespace
        try:
            source = (
                self._overlays[str(path)]
                if str(path) in self._overlays
                else path.read_text(encoding="utf-8")
            )
        except (OSError, UnicodeError) as exc:
            raise NameResolutionError(
                f"cannot read imported file {path}: {exc}", item.span
            ) from exc
        self._source_stack.append(path)
        try:
            program = parse_program(source)
            namespace = Namespace(item.path)
            start = len(self.checker._definitions)
            self.checker.check_imported_program(program, namespace, self._import_prelude, str(path))
            imported = ImportedSource(
                path, source, program, namespace, tuple(self.checker._definitions[start:])
            )
            self.imported_sources[path] = imported
            return namespace
        except SourceError:
            raise
        except HypomnesisError as exc:
            raise SourceError(exc, path, source) from exc
        finally:
            self._source_stack.pop()

    def _remember_definitions(self, definitions: list[ir.Definition]) -> None:
        known = {id(d) for d in self.definitions}
        self.definitions.extend(d for d in definitions if id(d) not in known)

    def _warnings(self, result: CheckResult, filename: str | None) -> None:
        result.warnings = [
            CompilerWarning(w.message, w.span, w.filename or filename) for w in result.warnings
        ]
        self.warnings.extend(result.warnings)

    def _run(self, result: CheckResult, filename: str | None = None) -> LoadResult:
        self._warnings(result, filename)
        self._remember_definitions(result.definitions)
        try:
            run_deep(lambda: self.interpreter.execute(result.definitions))
        except HypomnesisError:
            scheduled = {id(d) for d in result.definitions}
            self._failed_imports.update(
                path
                for path, imported in self.imported_sources.items()
                if any(id(d) in scheduled for d in imported.definitions)
            )
            raise
        self._executed_definitions.update(map(id, result.definitions))
        bindings = [
            self._binding(info, self.interpreter.globals[info.qname]) for info in result.values
        ]
        return LoadResult(bindings, result.types, result.warnings)

    def eval(self, source: str) -> Binding:
        """Evaluate an expression and return it as the binding ``it``."""
        expr = parse_expression(source)
        item = A.LetItem(False, (A.FunBinding("it", (), None, expr, span=expr.span),))
        result = self._run(self.checker.check_program(A.Program((item,))))
        return result.bindings[-1]

    def value(self, path: str) -> Value:
        return self.interpreter.globals[self.checker.lookup_value(path).qname]

    def type_of(self, path: str) -> str:
        return TypePrinter(self._public_type_names()).show(self.checker.lookup_value(path).scheme)

    def _public_type_names(self) -> dict[str, str]:
        names: dict[str, str] = {}

        def walk(namespace: Namespace, prefix: str) -> None:
            for name, info in namespace.types.items():
                names.setdefault(info.qname, prefix + name)
            for name, module in namespace.modules.items():
                walk(module, prefix + name + ".")

        walk(self.checker.root, "")
        return names

    def _binding(self, info: ValueInfo, value: Value) -> Binding:
        return Binding(
            info.name, info.qname, TypePrinter(self._public_type_names()).show(info.scheme), value
        )


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
