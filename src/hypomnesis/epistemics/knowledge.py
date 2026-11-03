"""Knowledge base: facts with provenance, unknowns, append-only journal, revision.

Statuses follow the three axes of note M3 §4.3:

* **existence** — a property is known, or an :class:`Unknown` (a metavariable
  that estimators and solvers propose values for);
* **support** — computed from provenance (:data:`provenance.SUPPORT`), never
  declared: a conclusion drawn from an estimate is itself estimated;
* **coherence** — conflicting values for the same property are reported.

Every change is an event appended to the journal; nothing is ever mutated in
place, so revisions keep the history (cahier des charges §7.3).
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from hypomnesis.epistemics.provenance import (
    BOOLEAN,
    CONFIDENCE,
    SUPPORT,
    Prov,
    Support,
    evaluate,
    obs,
)


@dataclass(frozen=True)
class Source:
    """Where a piece of information comes from (an observer, a model, a rule…)."""

    id: str
    kind: str  # "observation" | "estimation" | "default" | "hypothesis"
    origin: str  # human-readable: "demande utilisateur", "estimateur règle-empirique v1", …
    confidence: float = 1.0

    @property
    def support(self) -> Support:
        return {
            "observation": Support.OBSERVED,
            "estimation": Support.ESTIMATED,
            "default": Support.DEFAULTED,
            "hypothesis": Support.HYPOTHESIS,
        }[self.kind]


@dataclass(frozen=True)
class Fact:
    key: str  # "<objet>.<propriété>", par exemple "demande.largeur"
    value: Any
    provenance: Prov
    method: str  # how it was obtained: "observé", "estimé", "dérivé par solveur Z3", …
    premises: tuple[str, ...] = ()  # keys of the facts it was derived from


@dataclass(frozen=True)
class Unknown:
    key: str
    description: str


@dataclass(frozen=True)
class Event:
    seq: int
    kind: str  # "observed" | "estimated" | "derived" | "retracted" | "invalidated" | "unknown"
    key: str
    detail: str


@dataclass
class KnowledgeBase:
    sources: dict[str, Source] = field(default_factory=dict)
    facts: dict[str, Fact] = field(default_factory=dict)
    unknowns: dict[str, Unknown] = field(default_factory=dict)
    journal: list[Event] = field(default_factory=list)
    retracted: set[str] = field(default_factory=set)
    _ids: Any = field(default_factory=lambda: itertools.count(1), repr=False)

    # -------------------------------------------------------------- input

    def _log(self, kind: str, key: str, detail: str) -> None:
        self.journal.append(Event(len(self.journal) + 1, kind, key, detail))

    def _source(self, kind: str, origin: str, confidence: float) -> Source:
        source = Source(f"{kind[:3]}-{next(self._ids)}", kind, origin, confidence)
        self.sources[source.id] = source
        return source

    def unknown(self, key: str, description: str) -> Unknown:
        u = Unknown(key, description)
        self.unknowns[key] = u
        self._log("unknown", key, description)
        return u

    def observe(self, key: str, value: Any, origin: str) -> Fact:
        return self._record("observation", "observed", key, value, origin, 1.0, "observé")

    def estimate(self, key: str, value: Any, origin: str, confidence: float) -> Fact:
        return self._record("estimation", "estimated", key, value, origin, confidence, "estimé")

    def hypothesis(self, key: str, value: Any, origin: str, confidence: float) -> Fact:
        """An assumption: usable as a premise, withdrawn if contradicted."""
        return self._record("hypothesis", "hypothesis", key, value, origin, confidence, "hypothèse")

    def source_id(self, key: str) -> str:
        """The source of a fact recorded directly (observed, estimated, hypothesis)."""
        ids = list(dict.fromkeys(self.facts[key].provenance.observations()))
        if len(ids) != 1:
            raise ValueError(f"{key} n'a pas de source unique")
        return ids[0]

    def _record(self, kind, event, key, value, origin, confidence, method) -> Fact:
        source = self._source(kind, origin, confidence)
        fact = Fact(key, value, obs(source.id), f"{method} ({origin})")
        self._replace(key, fact)
        self._log(event, key, f"{value!r} — {origin} [{source.id}]")
        return fact

    def derive(self, key: str, value: Any, method: str, premises: list[str]) -> Fact:
        """A conclusion from existing facts: its provenance is the product of theirs."""
        provenance: Prov | None = None
        for premise in premises:
            p = self.facts[premise].provenance
            provenance = p if provenance is None else provenance * p
        fact = Fact(key, value, provenance or obs("axiome"), method, tuple(premises))
        self._replace(key, fact)
        self._log("derived", key, f"{value!r} — {method} ← {', '.join(premises)}")
        return fact

    def _replace(self, key: str, fact: Fact) -> None:
        self.facts[key] = fact
        self.unknowns.pop(key, None)

    # ----------------------------------------------------------- revision

    def retract_source(self, source_id: str, reason: str) -> list[str]:
        """Withdraw a source; invalidate every conclusion that depended on it.

        Implements the revision of §7.3 as the substitution ``x ↦ 0`` (P10, P11):
        a fact still holds iff its provenance evaluates to true without the source;
        facts that do not mention it are untouched.
        """
        self.retracted.add(source_id)
        self._log("retracted", source_id, reason)
        invalidated = []
        for key, fact in list(self.facts.items()):
            if not evaluate(fact.provenance, BOOLEAN, self._holds):
                del self.facts[key]
                self.unknowns[key] = Unknown(key, f"invalidée : {reason}")
                self._log("invalidated", key, f"dépendait de {source_id}")
                invalidated.append(key)
        return invalidated

    def _holds(self, source_id: str) -> bool:
        return source_id not in self.retracted and source_id in self.sources

    # ------------------------------------------------------------ queries

    def value(self, key: str) -> Any:
        return self.facts[key].value

    def support(self, key: str) -> Support:
        return evaluate(self.facts[key].provenance, SUPPORT, lambda s: self.sources[s].support)

    def confidence(self, key: str) -> float:
        return evaluate(
            self.facts[key].provenance, CONFIDENCE, lambda s: self.sources[s].confidence
        )

    def sources_of(self, key: str) -> list[Source]:
        ids = dict.fromkeys(self.facts[key].provenance.observations())
        return [self.sources[i] for i in ids]

    def explain(self, key: str, depth: int = 0) -> list[str]:
        """Why a fact holds, from its provenance: one line per fact, premises indented."""
        fact = self.facts[key]
        lines = [
            f"{'  ' * depth}- {key} = {fact.value!r} : {fact.method} "
            f"[support {self.support(key).label}, confiance {self.confidence(key):.2f}]"
        ]
        for premise in fact.premises:
            lines.extend(self.explain(premise, depth + 1))
        return lines

    def by_support(self, predicate: Callable[[Support], bool]) -> list[str]:
        return [k for k in self.facts if predicate(self.support(k))]
