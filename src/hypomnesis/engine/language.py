"""Loading an M2 language package into the engine (M3).

A language package is a directory with a manifest, ``langage.json``, validated
by ``contracts/schemas/language-manifest-1.0.0.json``:

* ``sources`` — Hypomnesis files defining the language (concepts, rules,
  estimators, constraints, command builders);
* ``contracts`` — JSON Schemas of its sensors and actuators;
* ``adapters`` — Python modules of the package connecting to the outside world
  (actuators, sensors, transcription stand-ins). Only files inside the package
  are loaded: a language cannot reach arbitrary Python;
* ``procedure`` — which generic engine procedure it uses, and how: names of
  Hypomnesis functions of the language, adapters, permissions.

The engine knows nothing about any particular language: everything specific
is named in the manifest and defined in the package.
"""

from __future__ import annotations

import importlib.util
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.runtime.values import Value
from hypomnesis.session import Session

MANIFEST = "langage.json"
MANIFEST_SCHEMA = "https://schemas.example.org/hypomnesis/language-manifest/1.0.0"


class LanguageError(ValueError):
    pass


@dataclass
class Language:
    root: Path
    manifest: dict[str, Any]
    schemas: SchemaRegistry
    session: Session = field(default_factory=Session)
    _adapters: dict[str, Any] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return self.manifest["name"]

    @property
    def procedure(self) -> dict[str, Any]:
        return self.manifest["procedure"]

    def function(self, path: str) -> Callable[..., Value]:
        """A Hypomnesis function of the language, callable from Python."""
        fn = self.session.value(path)
        return lambda *args: self.session.interpreter.apply(fn, list(args))

    def adapter(self, reference: str) -> Any:
        """``"adaptateurs/export.py:GeometryExport"`` → the attribute of that module."""
        file, _, attribute = reference.partition(":")
        path = (self.root / file).resolve()
        if self.root not in path.parents:
            raise LanguageError(f"adaptateur hors du paquet du langage : {file}")
        if file not in self._adapters:
            spec = importlib.util.spec_from_file_location(f"hyp_{self.name}_{path.stem}", path)
            if spec is None or spec.loader is None:
                raise LanguageError(f"adaptateur introuvable : {file}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self._adapters[file] = module
        try:
            return getattr(self._adapters[file], attribute)
        except AttributeError:
            raise LanguageError(f"{file} ne définit pas {attribute}") from None

    def load_program(self, source: str) -> None:
        """Load an M1 program written in this language."""
        self.session.load(source)


def load_language(root: Path) -> Language:
    root = root.resolve()
    manifest_path = root / MANIFEST
    if not manifest_path.exists():
        raise LanguageError(f"pas de {MANIFEST} dans {root}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schemas = SchemaRegistry.with_builtin_schemas()
    issues = schemas.issues(MANIFEST_SCHEMA, manifest)
    if issues:
        raise LanguageError("manifeste invalide : " + "; ".join(map(str, issues)))
    for contract in manifest.get("contracts", []):
        schemas.add(json.loads((root / contract).read_text(encoding="utf-8")))
    language = Language(root, manifest, schemas)
    for source in manifest["sources"]:
        language.session.load((root / source).read_text(encoding="utf-8"))
    return language
