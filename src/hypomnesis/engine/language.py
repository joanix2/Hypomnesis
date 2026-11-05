"""Load statically declared language layers and their symbolic definitions."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.adapters import AdapterRegistry
from hypomnesis.engine.errors import LanguageError, MissingDescriptionError, SourceError
from hypomnesis.engine.layers import LayerPlan, check_layers, package_file, resolve_layers
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.language.parser import parse_program
from hypomnesis.observability.trace import Tracer, current_tracer
from hypomnesis.runtime.values import Function, Value
from hypomnesis.session import Session

__all__ = ["Language", "LanguageError", "MissingDescriptionError", "load_language"]


@dataclass
class Language:
    root: Path
    manifest: dict[str, Any]
    schemas: SchemaRegistry
    session: Session
    plan: LayerPlan
    _adapters: AdapterRegistry | None = field(default=None, repr=False)

    @property
    def name(self) -> str:
        return self.manifest["name"]

    @property
    def procedure(self) -> dict[str, Any]:
        if "procedure" not in self.manifest:
            raise LanguageError(f"{self.name} est une bibliothèque sans procédure")
        return self.manifest["procedure"]

    @property
    def adapters(self) -> AdapterRegistry:
        """Only explicit execution/transcription requests may import Python modules."""
        if self._adapters is None:
            self._adapters = AdapterRegistry.load(self.root, self.manifest.get("adapters", []))
        return self._adapters

    def function(self, path: str) -> Callable[..., Value]:
        fn = self.session.value(path)
        return lambda *args: self.session.interpreter.apply(fn, list(args))

    def load_program(self, source: str, *, filename: str | None = None) -> None:
        tracer = current_tracer()
        with tracer.span("language.parse") if tracer is not None else nullcontext():
            program = parse_program(source)
        with tracer.span("language.typecheck") if tracer is not None else nullcontext():
            self.session.load_program(program, filename=filename, source_text=source)

    @contextmanager
    def trace_calls(self, tracer: Tracer) -> Iterator[None]:
        targets = {}
        for layer in self.plan.layers.values():
            for binding in layer.configuration.get("tracing", []):
                function = self.session.value(binding["function"])
                if not isinstance(function, Function):
                    raise LanguageError(f"fonction à tracer requise : {binding['function']}")
                attributes = {
                    "plugin": binding["function"],
                    "plugin.version": layer.configuration["version"],
                    "language": layer.name,
                }
                target = (binding["operation"], attributes)
                if id(function) in targets and targets[id(function)] != target:
                    raise LanguageError(f"instrumentation ambiguë : {binding['function']}")
                targets[id(function)] = target
        interpreter = self.session.interpreter
        previous = interpreter.call_context

        @contextmanager
        def scope(function: Function) -> Iterator[None]:
            target = targets.get(id(function))
            with (
                previous(function) if previous is not None else nullcontext(),
                tracer.span(target[0], **target[1]) if target else nullcontext(),
            ):
                yield

        if tracer.enabled and targets:
            interpreter.call_context = scope
        try:
            yield
        finally:
            interpreter.call_context = previous


def load_language(root: Path, *, strict: bool = True, execute: bool = True) -> Language:
    """Resolve and check each layer; optionally evaluate definitions, never adapters."""
    tracer = current_tracer()
    with tracer.span("language.parse") if tracer is not None else nullcontext():
        plan = resolve_layers(root)
    with tracer.span("language.typecheck") if tracer is not None else nullcontext():
        checked = check_layers(plan, strict=strict)
    schemas = SchemaRegistry.with_builtin_schemas()
    for reference in plan.root.configuration.get("contracts", []):
        path = package_file(plan.root.root, reference)
        try:
            schemas.add(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise LanguageError(f"contrat illisible {path} : {exc}") from exc
    if execute:
        session = Session()
        for source in plan.source_files():
            try:
                owner = next(layer for layer in plan.layers.values() if source in layer.sources)
                session.load_program(
                    source.program,
                    filename=str(source.path),
                    import_root=owner.root,
                    source_text=source.text,
                )
            except HypomnesisError as exc:
                if isinstance(exc, SourceError):
                    raise
                raise SourceError(exc, source.path, source.text) from exc
    else:
        session = checked
    return Language(plan.root.root, plan.root.configuration, schemas, session, plan)
