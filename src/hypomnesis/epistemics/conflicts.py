"""Declared incompatibilities over live evidence, independently of support."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
from typing import Literal

from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase, Source, _identifier
from hypomnesis.epistemics.metavariables import Proposal, ResolutionConflict, best_proposal
from hypomnesis.epistemics.provenance import BOOLEAN, SUPPORT, evaluate


@dataclass(frozen=True)
class Invariant:
    name: str
    keys: tuple[str, ...]
    accepts: Callable[[tuple[Fact, ...]], bool]

    def __post_init__(self) -> None:
        _identifier(self.name)
        _keys(self.keys)
        if not self.keys or not callable(self.accepts):
            raise ValueError("an invariant requires fact keys and a pure predicate")


def _keys(keys: tuple[str, ...]) -> None:
    if type(keys) is not tuple:
        raise ValueError("fact keys must be an immutable tuple")
    for key in keys:
        _identifier(key)
    if len(set(keys)) != len(keys):
        raise ValueError("fact keys must be distinct")


@dataclass(frozen=True)
class Conflict:
    rule: str
    kind: Literal["functional", "invariant"]
    facts: tuple[Fact, ...]
    sources: tuple[Source, ...]
    retracted_sources: tuple[str, ...]
    selection: Fact | None
    resolution: Literal["report", "best-support", "tied-best-support", "invariant"]


@dataclass(frozen=True)
class PendingCheck:
    rule: str
    missing: tuple[str, ...]


@dataclass(frozen=True)
class ConflictScan:
    conflicts: tuple[Conflict, ...] = ()
    checked: tuple[str, ...] = ()
    pending: tuple[PendingCheck, ...] = ()

    @property
    def coherence(self) -> Literal["conflict", "consistent", "unchecked"]:
        if self.conflicts:
            return "conflict"
        if self.pending or not self.checked:
            return "unchecked"
        return "consistent"


@dataclass(frozen=True)
class ConflictChecker:
    functional: tuple[str, ...] = ()
    invariants: tuple[Invariant, ...] = ()
    policy: Literal["report", "best-support"] = "report"

    def __post_init__(self) -> None:
        _keys(self.functional)
        if type(self.invariants) is not tuple or any(
            not isinstance(rule, Invariant) for rule in self.invariants
        ):
            raise ValueError("invariants must be an immutable tuple of Invariant")
        names = (*self.functional, *(rule.name for rule in self.invariants))
        if len(set(names)) != len(names):
            raise ValueError("conflict rule names must be distinct")
        if self.policy not in ("report", "best-support"):
            raise ValueError("unknown conflict resolution policy")

    def scan(self, base: KnowledgeBase) -> ConflictScan:
        claims = _claims(base)
        conflicts: list[Conflict] = []
        checked: list[str] = []
        pending: list[PendingCheck] = []
        for key in self.functional:
            facts = claims.get(key, ())
            if not facts:
                pending.append(PendingCheck(key, (key,)))
                continue
            checked.append(key)
            if any(not fact.same_value(facts[0]) for fact in facts[1:]):
                conflicts.append(self._report(base, key, "functional", facts))
        for rule in self.invariants:
            missing = tuple(key for key in rule.keys if key not in claims)
            if missing:
                pending.append(PendingCheck(rule.name, missing))
                continue
            checked.append(rule.name)
            for facts in product(*(claims[key] for key in rule.keys)):
                accepted = rule.accepts(facts)
                if type(accepted) is not bool:
                    raise ValueError(f"{rule.name}: invariant must return a bool")
                if not accepted:
                    conflicts.append(self._report(base, rule.name, "invariant", facts))
        return ConflictScan(tuple(conflicts), tuple(checked), tuple(pending))

    def _report(
        self,
        base: KnowledgeBase,
        rule: str,
        kind: Literal["functional", "invariant"],
        facts: tuple[Fact, ...],
    ) -> Conflict:
        identifiers = tuple(
            dict.fromkeys(source for fact in facts for source in fact.provenance.observations())
        )
        selection = None
        resolution: Literal["report", "best-support", "tied-best-support", "invariant"] = "report"
        if kind == "invariant":
            resolution = "invariant"
        elif self.policy == "best-support":
            proposals = tuple(
                Proposal(
                    fact,
                    evaluate(
                        fact.provenance,
                        SUPPORT,
                        lambda source: (
                            SUPPORT.zero
                            if source in base.retracted
                            else base.sources[source].support
                        ),
                    ),
                )
                for fact in facts
            )
            try:
                selection = best_proposal(proposals, rule).fact
                resolution = "best-support"
            except ResolutionConflict:
                resolution = "tied-best-support"
        return Conflict(
            rule,
            kind,
            facts,
            tuple(base.sources[source] for source in identifiers),
            tuple(source for source in identifiers if source in base.retracted),
            selection,
            resolution,
        )


def _claims(base: KnowledgeBase) -> dict[str, tuple[Fact, ...]]:
    # Current facts alone lose competing assertions overwritten at the same key.
    history = (event.fact for event in base.journal if event.fact is not None)
    candidates = dict.fromkeys((*history, *base.facts.values()))
    groups: dict[str, list[Fact]] = {}
    for fact in candidates:
        identifiers = set(fact.provenance.observations())
        missing = identifiers - base.sources.keys()
        if missing:
            raise ValueError(f"undeclared provenance sources: {sorted(missing)}")
        if evaluate(fact.provenance, BOOLEAN, lambda source: source not in base.retracted):
            groups.setdefault(fact.key, []).append(fact)
    return {key: tuple(facts) for key, facts in groups.items()}
