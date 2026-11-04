"""Explicit Python I/O bindings; decorators do not register global runtime state."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, TypeVar

from hypomnesis.engine.errors import LanguageError
from hypomnesis.engine.layers import package_file

F = TypeVar("F", bound=Callable[..., Any])
Role = Literal["sensor", "actuator", "environment", "transcriber"]
_MARKER = "__hypomnesis_binding__"


@dataclass(frozen=True)
class Binding:
    role: Role
    identifier: str


def _decorate(role: Role, identifier: str, function: F) -> F:
    if not identifier.strip():
        raise LanguageError("identifiant d'adaptateur vide")
    if hasattr(function, _MARKER):
        raise LanguageError("une fonction ne peut déclarer plusieurs adaptateurs")
    setattr(function, _MARKER, Binding(role, identifier))
    return function


def sensor(identifier: str) -> Callable[[F], F]:
    """Decorate a reader ``(environment, sensor_id) -> message envelope``."""
    return lambda function: _decorate("sensor", identifier, function)


def actuator(identifier: str) -> Callable[[F], F]:
    """Decorate a factory ``environment_or_output_path -> Actuator``."""
    return lambda function: _decorate("actuator", identifier, function)


def environment(function: F) -> F:
    """Decorate the factory ``(options, output_path) -> environment``."""
    return _decorate("environment", "environment", function)


def transcriber(function: F) -> F:
    """Decorate the optional deterministic ``request -> M1 source`` adapter."""
    return _decorate("transcriber", "transcriber", function)


@dataclass
class AdapterRegistry:
    bindings: dict[tuple[Role, str], Callable[..., Any]] = field(default_factory=dict)

    def get(self, role: Role, identifier: str | None = None) -> Callable[..., Any]:
        key = role, identifier or role
        if key not in self.bindings:
            raise LanguageError(f"adaptateur non déclaré : {role} {key[1]}")
        return self.bindings[key]

    def identifiers(self, role: Role) -> list[str]:
        return sorted(identifier for kind, identifier in self.bindings if kind == role)

    @classmethod
    def load(cls, root: Path, references: list[str]) -> AdapterRegistry:
        registry = cls()
        for reference in references:
            path = package_file(root, reference)
            if path.suffix != ".py" or not path.is_file():
                raise LanguageError(f"module Python d'adaptateurs introuvable : {path}")
            name = "_hyp_adapter_" + sha256(str(path).encode()).hexdigest()
            spec = importlib.util.spec_from_file_location(name, path)
            if spec is None or spec.loader is None:
                raise LanguageError(f"adaptateur introuvable : {path}")
            module = importlib.util.module_from_spec(spec)
            previous = sys.modules.get(name)
            sys.modules[name] = module
            loaded = False
            try:
                spec.loader.exec_module(module)
                loaded = True
            finally:
                if not loaded:
                    if previous is None:
                        sys.modules.pop(name, None)
                    else:
                        sys.modules[name] = previous
            found = False
            for function in vars(module).values():
                binding = getattr(function, _MARKER, None)
                if not isinstance(binding, Binding) or not callable(function):
                    continue
                if getattr(function, "__module__", None) != module.__name__:
                    continue
                found = True
                key = binding.role, binding.identifier
                if registry.bindings.get(key) is function:
                    continue
                if key in registry.bindings:
                    raise LanguageError(f"{path} : adaptateur dupliqué {key}")
                arity = 2 if binding.role in ("sensor", "environment") else 1
                try:
                    inspect.signature(function).bind(*([None] * arity))
                except (TypeError, ValueError) as exc:
                    raise LanguageError(f"{path} : signature incompatible pour {key}") from exc
                if inspect.iscoroutinefunction(function):
                    raise LanguageError(
                        f"{path} : adaptateur asynchrone non pris en charge : {key}"
                    )
                registry.bindings[key] = function
            if not found:
                raise LanguageError(f"{path} : aucun adaptateur décoré")
        return registry
