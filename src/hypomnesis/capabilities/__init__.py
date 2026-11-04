"""Capability interfaces (cahier des charges §6, m3-metalangage §4.4): engine side, backend-free."""

from __future__ import annotations

from hypomnesis.capabilities.protocols import (
    ROLES,
    Actuator,
    Estimator,
    Generator,
    KnowledgeBase,
    Observer,
    Resolver,
    Solver,
    Transpiler,
    Validator,
    roles_of,
)
from hypomnesis.capabilities.result import (
    Certificate,
    Diagnostic,
    Result,
    Severity,
    failure,
    success,
)
from hypomnesis.capabilities.safe import RAISED, guarded

__all__ = [
    "RAISED",
    "ROLES",
    "Actuator",
    "Certificate",
    "Diagnostic",
    "Estimator",
    "Generator",
    "KnowledgeBase",
    "Observer",
    "Resolver",
    "Result",
    "Severity",
    "Solver",
    "Transpiler",
    "Validator",
    "failure",
    "guarded",
    "roles_of",
    "success",
]
