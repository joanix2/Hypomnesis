"""Load statically declared language layers and their symbolic definitions."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.adapters import AdapterRegistry
from hypomnesis.engine.errors import LanguageError, MissingDescriptionError, SourceError
from hypomnesis.engine.layers import LayerPlan, check_layers, package_file, resolve_layers
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.runtime.values import Value
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

    def load_program(self, source: str) -> None:
        self.session.load(source)


def load_language(root: Path, *, strict: bool = True, execute: bool = True) -> Language:
    """Resolve and check each layer; optionally evaluate definitions, never adapters."""
    plan = resolve_layers(root)
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
                session.load_program(source.program, filename=str(source.path))
            except HypomnesisError as exc:
                raise SourceError(exc, source.path, source.text) from exc
    else:
        session = checked
    return Language(plan.root.root, plan.root.configuration, schemas, session, plan)
