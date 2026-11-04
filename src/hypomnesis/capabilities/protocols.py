# pyright: strict
"""The nine generic capability interfaces (cahier des charges §6).

Each interface is a structural ``typing.Protocol``: a plugin conforms by shape, without
inheriting, and without importing any backend (§6.2). Each docstring gives the interface's
type-theoretic role from docs/architecture/m3-metalangage.md §4.4, where Hypomnesis is an
*elaborator* and plugins are tactics.

Common contract: every method returns a ``Result`` and reports failure through its diagnostics;
only the kernel decides (§4.5), so a plugin returns values and certificates, never facts.
Input type parameters are contravariant, output ones covariant.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, TypeVar, runtime_checkable

from hypomnesis.capabilities.result import Result

In = TypeVar("In", contravariant=True)
Out = TypeVar("Out", covariant=True)
Fact = TypeVar("Fact")


@runtime_checkable
class Observer(Protocol[In, Out]):
    """§6 « acquérir des observations »; §4.4: introduces axioms of grade ``Observed``."""

    def observe(self, query: In, /) -> Result[Out]: ...


@runtime_checkable
class Generator(Protocol[In, Out]):
    """§6 « générer des candidats »; §4.4: enumerates inhabitants of a type (term synthesis)."""

    def generate(self, spec: In, /, *, limit: int) -> Result[Sequence[Out]]: ...


@runtime_checkable
class Estimator(Protocol[In, Out]):
    """§6 « proposer des valeurs inconnues »; §4.4: proposes a solution for a metavariable.

    The kernel grades the proposed value ``Estimated``; the plugin cannot claim a grade.
    """

    def estimate(self, unknown: In, /) -> Result[Out]: ...


@runtime_checkable
class Transpiler(Protocol[In, Out]):
    """§6 « transformer une représentation »; §4.4: a morphism of theories (§6.1 signatures)."""

    def transpile(self, source: In, /) -> Result[Out]: ...


@runtime_checkable
class Solver(Protocol[In, Out]):
    """§6 « rechercher une solution »; §4.4: solves a set of metavariables under constraints."""

    def solve(self, problem: In, /) -> Result[Out]: ...


@runtime_checkable
class Validator(Protocol[In, Out]):
    """§6 « vérifier une proposition »; §4.4: a decision procedure.

    Accepting returns the checked proposal with a proof ``certificate``; refusing returns an
    error diagnostic whose ``data`` carries the counterexample.
    """

    def validate(self, proposal: In, /) -> Result[Out]: ...


@runtime_checkable
class KnowledgeBase(Protocol[Fact]):
    """§6 « interroger et conserver des connaissances »; §4.4: the persistent context ``Γ``."""

    def query(self, question: object, /) -> Result[Sequence[Fact]]: ...

    def store(self, fact: Fact, /) -> Result[None]: ...


@runtime_checkable
class Actuator(Protocol[In, Out]):
    """§6 « déclencher une opération extérieure autorisée »; §4.4: an algebraic-effect operation.

    Reached only through the controlled dispatcher (§9.7), never directly by a program.
    """

    def actuate(self, command: In, /) -> Result[Out]: ...


@runtime_checkable
class Resolver(Protocol[In, Out]):
    """§6 « orchestrer les capacités pour atteindre un objectif »; §4.4: a tactic.

    ``capabilities`` maps identifiers to the plugins it may compose.
    """

    def resolve(self, goal: In, capabilities: Mapping[str, object], /) -> Result[Out]: ...


# Keyed by the ``role`` enum of the extension manifest (contracts/schemas/extension-manifest).
ROLES: Mapping[str, type[object]] = {
    "Observer": Observer,
    "Generator": Generator,
    "Estimator": Estimator,
    "Transpiler": Transpiler,
    "Solver": Solver,
    "Validator": Validator,
    "KnowledgeBase": KnowledgeBase,
    "Actuator": Actuator,
    "Resolver": Resolver,
}


def roles_of(plugin: object) -> tuple[str, ...]:
    """Roles whose interface ``plugin`` structurally satisfies (method presence only)."""
    return tuple(role for role, protocol in ROLES.items() if isinstance(plugin, protocol))
