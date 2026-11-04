# pyright: strict
"""Containment of plugin failures: no raw exception reaches the kernel (cahier des charges §6)."""

from __future__ import annotations

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from hypomnesis.capabilities.result import Diagnostic, Result, failure

P = ParamSpec("P")
T = TypeVar("T")

RAISED = "capability.raised"


def guarded(call: Callable[P, Result[T]]) -> Callable[P, Result[T]]:
    """Wrap a plugin method so that an exception becomes a failed ``Result``.

    ``Exception`` only: ``KeyboardInterrupt`` and ``SystemExit`` still propagate.
    """

    @functools.wraps(call)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Result[T]:
        try:
            return call(*args, **kwargs)
        except Exception as exc:
            name = type(exc).__name__
            return failure(Diagnostic(RAISED, f"{name}: {exc}", data={"exception": name}))

    return wrapper
