"""Provenance as free semiring terms (Green, Karvounarakis, Tannen, PODS 2007).

Mirrors ``formal/Hypomnesis/Epistemics/Provenance.lean``: a conclusion's
provenance is a term over observation identifiers, ``times`` for premises used
jointly and ``plus`` for alternative derivations. Every reading (support grade,
"does it still hold", confidence) is an evaluation in a semiring, and revision
is substitution. The properties proved in Lean (``eval_subst``,
``holds_after_retract``, ``retract_unrelated``, ``support_mono``) are tested on
this implementation in ``tests/property/test_provenance.py``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import IntEnum
from math import inf
from typing import Generic, TypeVar

K = TypeVar("K")


class Prov:
    """A provenance term. Build with :func:`obs`, ``ZERO``, ``ONE``, ``+`` and ``*``."""

    __slots__ = ()

    def __add__(self, other: Prov) -> Prov:
        return Plus(self, other)

    def __mul__(self, other: Prov) -> Prov:
        return Times(self, other)

    def observations(self) -> Iterator[str]:
        if isinstance(self, Obs):
            yield self.id
        elif isinstance(self, Plus | Times):
            yield from self.left.observations()
            yield from self.right.observations()


@dataclass(frozen=True, slots=True)
class Obs(Prov):
    id: str


@dataclass(frozen=True, slots=True)
class Zero(Prov):
    pass


@dataclass(frozen=True, slots=True)
class One(Prov):
    pass


@dataclass(frozen=True, slots=True)
class Plus(Prov):
    left: Prov
    right: Prov


@dataclass(frozen=True, slots=True)
class Times(Prov):
    left: Prov
    right: Prov


ZERO = Zero()
ONE = One()


def obs(identifier: str) -> Obs:
    return Obs(identifier)


@dataclass(frozen=True)
class Semiring(Generic[K]):
    zero: K
    one: K
    add: Callable[[K, K], K]
    mul: Callable[[K, K], K]


def evaluate(p: Prov, semiring: Semiring[K], valuation: Callable[[str], K]) -> K:
    if isinstance(p, Obs):
        return valuation(p.id)
    if isinstance(p, Zero):
        return semiring.zero
    if isinstance(p, One):
        return semiring.one
    if isinstance(p, Plus):
        return semiring.add(
            evaluate(p.left, semiring, valuation), evaluate(p.right, semiring, valuation)
        )
    assert isinstance(p, Times)
    return semiring.mul(
        evaluate(p.left, semiring, valuation), evaluate(p.right, semiring, valuation)
    )


def substitute(p: Prov, sigma: Callable[[str], Prov]) -> Prov:
    if isinstance(p, Obs):
        return sigma(p.id)
    if isinstance(p, Plus):
        return Plus(substitute(p.left, sigma), substitute(p.right, sigma))
    if isinstance(p, Times):
        return Times(substitute(p.left, sigma), substitute(p.right, sigma))
    return p


def retract(identifier: str) -> Callable[[str], Prov]:
    """Substitution removing one observation (``x ↦ 0``)."""
    return lambda x: ZERO if x == identifier else Obs(x)


# ------------------------------------------------------------- semirings


class Support(IntEnum):
    """Support grade (higher = weaker), the « support » axis of note M3 §4.3."""

    OBSERVED = 0
    ESTIMATED = 1
    DEFAULTED = 2
    HYPOTHESIS = 3
    UNSUPPORTED = 4

    @property
    def label(self) -> str:
        return {
            Support.OBSERVED: "observé",
            Support.ESTIMATED: "estimé",
            Support.DEFAULTED: "par défaut",
            Support.HYPOTHESIS: "hypothèse",
            Support.UNSUPPORTED: "non fondé",
        }[self]


SUPPORT: Semiring[Support] = Semiring(
    zero=Support.UNSUPPORTED,
    one=Support.OBSERVED,
    add=min,  # the best alternative derivation wins
    mul=max,  # joint use: the weakest premise wins
)

BOOLEAN: Semiring[bool] = Semiring(False, True, lambda a, b: a or b, lambda a, b: a and b)

#: Viterbi semiring: confidence of the best derivation.
CONFIDENCE: Semiring[float] = Semiring(0.0, 1.0, max, lambda a, b: a * b)

#: Tropical semiring on nonnegative costs: cheapest alternative, summed premises.
#: ``inf`` means no derivation, and a premise-free proof has zero cost.
COST: Semiring[float] = Semiring(inf, 0.0, min, lambda a, b: a + b)
