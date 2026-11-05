"""Persistent typed holes; proposal quality never erases conflicting evidence."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Literal

from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.epistemics.knowledge import Fact
from hypomnesis.epistemics.provenance import Prov, Support
from hypomnesis.language.typesystem.types import TCon
from hypomnesis.runtime.values import Value


class UnresolvedMetaVar(ValueError):
    pass


class ResolutionConflict(ValueError):
    pass


@dataclass(frozen=True)
class Constraint:
    name: str
    accepts: Callable[[Value], bool]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip() or not callable(self.accepts):
            raise ValueError("a constraint requires a name and a predicate")


@dataclass(frozen=True)
class Proposal:
    fact: Fact
    grade: Support

    def __post_init__(self) -> None:
        if not isinstance(self.fact, Fact) or not isinstance(self.grade, Support):
            raise ValueError("a proposal requires a concrete fact and a support grade")
        if self.grade == Support.UNSUPPORTED:
            raise ValueError("a proposal requires evidence")


@dataclass(frozen=True)
class MetaVar:
    id: str
    codec: TypeCodec = field(repr=False)
    constraints: tuple[Constraint, ...] = ()
    proposals: tuple[Proposal, ...] = ()
    _selection: int | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("a metavariable requires a non-empty identifier")
        if not isinstance(self.codec, TypeCodec):
            raise ValueError("a metavariable requires a closed host TypeCodec")
        if type(self.constraints) is not tuple or any(
            not isinstance(c, Constraint) for c in self.constraints
        ):
            raise ValueError("constraints must be an immutable tuple of Constraint")
        if len({c.name for c in self.constraints}) != len(self.constraints):
            raise ValueError("constraint names must be distinct")
        if type(self.proposals) is not tuple:
            raise ValueError("proposals must be an immutable tuple")
        for proposal in self.proposals:
            if not isinstance(proposal, Proposal) or proposal.fact.key != self.id:
                raise ValueError("proposal belongs to a different metavariable")
            self.codec.encode(proposal.fact.value)
            for constraint in self.constraints:
                if constraint.accepts(proposal.fact.value) is not True:
                    raise ValueError(f"{self.id}: constraint violated: {constraint.name}")
        if self._selection is not None and (
            type(self._selection) is not int or not 0 <= self._selection < len(self.proposals)
        ):
            raise ValueError("resolution must select an existing proposal")

    @property
    def type(self) -> TCon:
        return self.codec.type

    @property
    def state(self) -> Literal["unresolved", "proposed", "resolved"]:
        if self._selection is not None:
            return "resolved"
        return "proposed" if self.proposals else "unresolved"

    @property
    def selected(self) -> Proposal | None:
        return None if self._selection is None else self.proposals[self._selection]

    @property
    def value(self) -> Value:
        selected = self.selected
        if selected is None:
            raise UnresolvedMetaVar(f"{self.id}: no concrete value before resolution")
        return selected.fact.value

    @property
    def grade(self) -> Support | None:
        selected = self.selected
        return None if selected is None else selected.grade

    @property
    def coherence(self) -> Literal["consistent", "conflict"]:
        return "conflict" if conflict(self) else "consistent"


def propose(meta: MetaVar, value: Value, grade: Support, provenance: Prov) -> MetaVar:
    fact = Fact(meta.id, value, provenance, "proposal")
    candidate = Proposal(fact, grade)
    return replace(meta, proposals=(*meta.proposals, candidate), _selection=None)


def conflict(meta: MetaVar) -> bool:
    return bool(meta.proposals) and any(
        not p.fact.same_value(meta.proposals[0].fact) for p in meta.proposals[1:]
    )


def best(meta: MetaVar) -> Proposal:
    return best_proposal(meta.proposals, meta.id)


def best_proposal(proposals: tuple[Proposal, ...], key: str) -> Proposal:
    if not proposals:
        raise UnresolvedMetaVar(f"{key}: no proposal")
    grade = min(p.grade for p in proposals)
    candidates = [p for p in proposals if p.grade == grade]
    if any(not p.fact.same_value(candidates[0].fact) for p in candidates[1:]):
        raise ResolutionConflict(f"{key}: incompatible best-supported proposals")
    return candidates[0]


def resolve(meta: MetaVar, *, choice: int | None = None) -> MetaVar:
    if choice is None:
        if conflict(meta):
            raise ResolutionConflict(
                f"{meta.id}: explicit choice required for conflicting evidence"
            )
        choice = meta.proposals.index(best(meta))
    return replace(meta, _selection=choice)
