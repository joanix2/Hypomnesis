# pyright: strict
"""Structured result of a capability call (cahier des charges §6, m3-metalangage §4.5).

A plugin never decides anything: it returns a *value*, optionally a *certificate* the kernel can
check, and *diagnostics*. A call reports failure through ``Result``, never through an exception.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Generic, Never, TypeVar

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """A message about a call; ``data`` carries structured detail (e.g. a counterexample)."""

    code: str
    message: str
    severity: Severity = Severity.ERROR
    data: Mapping[str, object] = field(default_factory=lambda: {})


@dataclass(frozen=True, slots=True)
class Certificate:
    """Evidence the kernel checks instead of trusting the plugin (model, proof, trace…)."""

    kind: str
    body: Mapping[str, object] = field(default_factory=lambda: {})


@dataclass(frozen=True, slots=True)
class Result(Generic[T_co]):
    """Value, certificate and diagnostics of one capability call.

    ``ok`` holds when no diagnostic has severity ``error``; ``value`` is then meaningful.
    """

    value: T_co | None = None
    certificate: Certificate | None = None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def ok(self) -> bool:
        return all(d.severity is not Severity.ERROR for d in self.diagnostics)


def success(
    value: T,
    *,
    certificate: Certificate | None = None,
    diagnostics: Iterable[Diagnostic] = (),
) -> Result[T]:
    """A successful result; ``diagnostics`` may still carry warnings or notes."""
    return Result(value, certificate, tuple(diagnostics))


def failure(diagnostic: Diagnostic, *more: Diagnostic) -> Result[Never]:
    """A failed result (``Result`` is covariant, so it fits any ``Result[T]``)."""
    return Result(None, None, (diagnostic, *more))
