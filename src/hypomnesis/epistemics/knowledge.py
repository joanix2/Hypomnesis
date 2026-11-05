"""Knowledge base: facts with provenance, unknowns, append-only journal, revision.

Statuses follow the three axes of note M3 §4.3:

* **existence** — a property is known, or an :class:`Unknown` (a metavariable
  that estimators and solvers propose values for);
* **support** — computed from provenance (:data:`provenance.SUPPORT`), never
  declared: a conclusion drawn from an estimate is itself estimated;
* **coherence** — conflicting values for the same property are reported.

Every change is an event appended to the journal; nothing is ever mutated in
place, so revisions keep the history (cahier des charges §7.3).

The provenance terms stay the source of truth for support, confidence and "does
it still hold". :meth:`KnowledgeBase.graph` derives from them a NetworkX
dependency graph (source → fact, premise → conclusion) for explanations and
node-link export. Revision uses the inverse observation index in ``revision``;
its final verdict remains Boolean evaluation of provenance, which is exact
when a fact has several derivations.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import networkx as nx

from hypomnesis.epistemics.provenance import (
    CONFIDENCE,
    SUPPORT,
    Obs,
    One,
    Plus,
    Prov,
    Support,
    Times,
    Zero,
    evaluate,
    obs,
)
from hypomnesis.epistemics.revision import invalidated
from hypomnesis.runtime.values import RecordValue, Variant

if TYPE_CHECKING:
    from hypomnesis.epistemics.conflicts import ConflictChecker, ConflictScan

FACT = "fact:"  # node-id prefixes: a fact key may look like a source id
SOURCE = "source:"
AXIOM = "axiome"  # id of the declared source of premise-less facts (never retracted)


def _identifier(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("expected a non-empty identifier")


def _snapshot(value: Any, active: frozenset[int] = frozenset()) -> tuple[str, Any]:
    if value is None or type(value) in (str, bool, int):
        return type(value).__name__, value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("knowledge values must be finite")
        return "float", value
    if id(value) in active:
        raise ValueError("cyclic knowledge value")
    active = active | {id(value)}
    if type(value) in (list, tuple):
        return type(value).__name__, tuple(_snapshot(v, active) for v in value)
    if type(value) is dict:
        if any(not isinstance(k, str) for k in value):
            raise ValueError("knowledge object keys must be strings")
        return "dict", tuple((k, _snapshot(v, active)) for k, v in value.items())
    if type(value) is RecordValue:
        _identifier(value.type_name)
        if not isinstance(value.fields, tuple) or any(
            not isinstance(pair, tuple) or len(pair) != 2 for pair in value.fields
        ):
            raise ValueError("invalid record fields")
        for key, _ in value.fields:
            _identifier(key)
        return "record", (value.type_name, _snapshot(value.fields, active))
    if type(value) is Variant:
        _identifier(value.tag)
        if type(value.index) is not int or value.index < 0:
            raise ValueError("invalid constructor index")
        return "variant", (value.tag, _snapshot(value.arg, active), value.index)
    raise ValueError(f"unsupported knowledge value: {type(value).__name__}")


def _restore(snapshot: tuple[str, Any]) -> Any:
    kind, data = snapshot
    if kind in ("NoneType", "str", "bool", "int", "float"):
        return data
    if kind == "dict":
        return {k: _restore(v) for k, v in data}
    if kind == "record":
        return RecordValue(data[0], _restore(data[1]))
    if kind == "variant":
        return Variant(data[0], _restore(data[1]), data[2])
    items = tuple(_restore(v) for v in data)
    return list(items) if kind == "list" else items


def _same_value(left: tuple[str, Any], right: tuple[str, Any]) -> bool:
    kind, lhs = left
    if kind != right[0]:
        return False
    rhs = right[1]
    if kind == "dict":
        a, b = dict(lhs), dict(rhs)
        return a.keys() == b.keys() and all(_same_value(a[k], b[k]) for k in a)
    if kind in ("list", "tuple"):
        return len(lhs) == len(rhs) and all(
            _same_value(a, b) for a, b in zip(lhs, rhs, strict=True)
        )
    if kind == "record":
        return lhs[0] == rhs[0] and _same_value(lhs[1], rhs[1])
    if kind == "variant":
        return lhs[0] == rhs[0] and lhs[2] == rhs[2] and _same_value(lhs[1], rhs[1])
    return lhs == rhs


def _provenance(value: Prov) -> Prov:
    if type(value) is Obs:
        _identifier(value.id)
        return value
    if type(value) in (Zero, One):
        return value
    if isinstance(value, Plus | Times):
        constructor = Plus if isinstance(value, Plus) else Times
        return constructor(_provenance(value.left), _provenance(value.right))
    raise ValueError("invalid provenance term")


@dataclass(frozen=True)
class Source:
    """Where a piece of information comes from (an observer, a model, a rule…)."""

    id: str
    kind: str  # "observation" | "estimation" | "default" | "hypothesis"
    origin: str  # human-readable: "demande utilisateur", "estimateur règle-empirique v1", …
    confidence: float = 1.0

    def __post_init__(self) -> None:
        _identifier(self.id)
        _identifier(self.origin)
        if self.kind not in ("observation", "estimation", "default", "hypothesis"):
            raise ValueError(f"invalid source kind: {self.kind}")
        if type(self.confidence) not in (int, float) or not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be a finite number between 0 and 1")

    @property
    def support(self) -> Support:
        return {
            "observation": Support.OBSERVED,
            "estimation": Support.ESTIMATED,
            "default": Support.DEFAULTED,
            "hypothesis": Support.HYPOTHESIS,
        }[self.kind]


@dataclass(frozen=True, init=False)
class Fact:
    """Immutable snapshot of a concrete value with its justification.

    v0.3 §7.1: Observed/Estimated/Defaulted/Hypothesis are readings of source
    provenance, not stored grades. Derived is the method/premise justification,
    Unknown is a separate metavariable, and Conflict belongs to coherence
    (detection is HYP-035). A Fact does not assert absence of conflicts.

    ``key`` is the stable logical property identifier, not a revision number.
    Input containers are snapshotted; ``value`` returns detached containers.
    JSON exchange is typed through ``epistemics.serialization`` and TypeCodec.
    """

    key: str  # "<objet>.<propriété>", par exemple "demande.largeur"
    _value: tuple[str, Any] = field(repr=False)
    provenance: Prov
    method: str  # how it was obtained: "observé", "estimé", "dérivé par solveur Z3", …
    premises: tuple[str, ...] = ()  # keys of the facts it was derived from

    def __init__(
        self, key: str, value: Any, provenance: Prov, method: str, premises: tuple[str, ...] = ()
    ) -> None:
        _identifier(key)
        _identifier(method)
        if not isinstance(premises, tuple):
            raise ValueError("premises must be an immutable tuple")
        for premise in premises:
            _identifier(premise)
        object.__setattr__(self, "key", key)
        object.__setattr__(self, "_value", _snapshot(value))
        object.__setattr__(self, "provenance", _provenance(provenance))
        object.__setattr__(self, "method", method)
        object.__setattr__(self, "premises", premises)

    @property
    def value(self) -> Any:
        return _restore(self._value)

    def same_value(self, other: Fact) -> bool:
        return _same_value(self._value, other._value)


@dataclass(frozen=True)
class Unknown:
    """Unresolved metavariable identified by key, never a concrete sentinel."""

    key: str
    description: str

    def __post_init__(self) -> None:
        _identifier(self.key)
        _identifier(self.description)


@dataclass(frozen=True)
class Observation:
    """An observed Fact and its declared Source; ``id`` survives JSON exchange."""

    source: Source
    fact: Fact

    def __post_init__(self) -> None:
        if not isinstance(self.source, Source) or not isinstance(self.fact, Fact):
            raise ValueError("observation requires a Source and a Fact")
        if (
            self.source.kind != "observation"
            or self.fact.provenance != obs(self.source.id)
            or self.fact.premises
        ):
            raise ValueError("observation must directly reference its observation source")

    @property
    def id(self) -> str:
        return self.source.id


@dataclass(frozen=True)
class Event:
    seq: int
    kind: str  # "observed" | "estimated" | "derived" | "retracted" | "invalidated" | "unknown"
    key: str
    detail: str
    fact: Fact | None = None
    unknown: Unknown | None = None


@dataclass
class KnowledgeBase:
    sources: dict[str, Source] = field(default_factory=dict)
    facts: dict[str, Fact] = field(default_factory=dict)
    unknowns: dict[str, Unknown] = field(default_factory=dict)
    _journal: list[Event] = field(default_factory=list, init=False, repr=False)
    retracted: set[str] = field(default_factory=set)
    _next_source_id: int = field(default=1, init=False, repr=False)
    conflict_checker: ConflictChecker | None = field(default=None, repr=False)

    # -------------------------------------------------------------- input

    @property
    def journal(self) -> tuple[Event, ...]:
        """Read-only history; events and their concrete fact snapshots are frozen."""
        return tuple(self._journal)

    def _log(
        self,
        kind: str,
        key: str,
        detail: str,
        fact: Fact | None = None,
        *,
        unknown: Unknown | None = None,
    ) -> None:
        self._journal.append(Event(len(self._journal) + 1, kind, key, detail, fact, unknown))

    def _source(self, kind: str, origin: str, confidence: float) -> Source:
        while True:
            identifier = f"{kind[:3]}-{self._next_source_id}"
            self._next_source_id += 1
            source = Source(identifier, kind, origin, confidence)
            if identifier not in self.sources and identifier not in self.retracted:
                return source

    def unknown(self, key: str, description: str) -> Unknown:
        u = Unknown(key, description)
        self.unknowns[key] = u
        self._log("unknown", key, description, unknown=u)
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
        self.sources[source.id] = source
        self._replace(key, fact)
        self._log(event, key, f"{value!r} — {origin} [{source.id}]", fact)
        return fact

    def derive(self, key: str, value: Any, method: str, premises: list[str]) -> Fact:
        """A conclusion from existing facts: its provenance is the product of theirs.

        A conclusion without premises is a *program constant* (HYP-143, option A): it
        rests on the declared source :data:`AXIOM` — kind ``default``, support
        « par défaut », confidence 1 — which is never retracted, so the fact survives
        the retraction of any other source and keeps a readable support.
        """
        provenance = self.provenance_of(premises)
        fact = Fact(key, value, provenance, method, tuple(premises))
        if not premises:
            self._declare_axiom()
        self._replace(key, fact)
        self._log("derived", key, f"{value!r} — {method} ← {', '.join(premises)}", fact)
        return fact

    def provenance_of(self, premises: tuple[str, ...] | list[str]) -> Prov:
        provenance: Prov | None = None
        for premise in premises:
            p = self.facts[premise].provenance
            provenance = p if provenance is None else provenance * p
        return obs(AXIOM) if provenance is None else provenance

    def publish_fact(self, fact: Fact, *, sources: tuple[Source, ...] = ()) -> None:
        """Publish a validated derivation and its new sources atomically."""
        if not isinstance(fact, Fact) or type(sources) is not tuple:
            raise ValueError("publication requires a Fact and an immutable tuple of sources")
        pending: dict[str, Source] = {}
        for source in sources:
            if not isinstance(source, Source):
                raise ValueError("publication requires valid sources")
            previous = pending.get(source.id, self.sources.get(source.id))
            if previous is not None and previous != source:
                raise ValueError(f"source {source.id} is already declared differently")
            pending[source.id] = source
        identifiers = set(fact.provenance.observations())
        if AXIOM in identifiers or AXIOM in pending:
            axiom = Source(AXIOM, "default", "constante du programme", 1.0)
            if pending.get(AXIOM, self.sources.get(AXIOM, axiom)) != axiom:
                raise ValueError("incompatible program axiom source")
            if AXIOM not in self.sources:
                pending[AXIOM] = axiom
        unknown = identifiers - (self.sources.keys() | pending.keys())
        if unknown:
            raise ValueError(f"undeclared provenance sources: {sorted(unknown)}")
        missing = [key for key in fact.premises if key not in self.facts]
        if missing:
            raise ValueError(f"missing premises: {missing}")
        self.sources.update(pending)
        self._replace(fact.key, fact)
        self._log("derived", fact.key, fact.method, fact)

    def _declare_axiom(self) -> None:
        if AXIOM not in self.sources:
            self.sources[AXIOM] = Source(AXIOM, "default", "constante du programme", 1.0)

    def _replace(self, key: str, fact: Fact) -> None:
        if key in self.facts:
            self._log("replaced", key, "ancienne conclusion conservée", self.facts[key])
        self.facts[key] = fact
        self.unknowns.pop(key, None)

    # ----------------------------------------------------------- revision

    def retract_source(self, source_id: str, reason: str) -> list[str]:
        """Withdraw a source; invalidate every conclusion that depended on it.

        Implements the revision of §7.3 as the substitution ``x ↦ 0`` (P10, P11):
        a fact still holds iff its provenance evaluates to true without the source;
        facts that do not mention it are untouched. The :data:`AXIOM` source of
        premise-less facts cannot be retracted.
        """
        if source_id == AXIOM:
            raise ValueError(f"la source {AXIOM!r} (constantes du programme) n'est pas rétractable")
        self.retracted.add(source_id)
        self._log("retracted", source_id, reason)
        keys = invalidated(self.facts, self.retracted)
        for key in keys:
            fact = self.facts.pop(key)
            self.unknowns[key] = Unknown(key, f"invalidée : {reason}")
            self._log(
                "invalidated",
                key,
                f"dépendait de {source_id}",
                fact,
                unknown=self.unknowns[key],
            )
        return keys

    def replace_observation(self, key: str, value: Any, origin: str, reason: str) -> Fact:
        """Retract a direct observation and invalidate its dependent conclusions.

        The new value does not silently re-execute derivation methods. Invalidated
        properties remain metavariables until rules or the caller derive them again.
        """
        source_id = self.source_id(key)
        if self.sources[source_id].kind != "observation":
            raise ValueError("only a direct observation can be replaced")
        old = self.facts[key]
        if old.provenance != obs(source_id) or old.premises:
            raise ValueError("only a direct observation can be replaced")
        Source("validation", "observation", origin)
        Fact(key, value, obs(source_id), "validation")
        self._log("replaced", key, reason, old)
        self.retract_source(source_id, reason)
        new = self.observe(key, value, origin)
        self._log("revised", key, reason, new)
        return new

    def _holds(self, source_id: str) -> bool:
        # A source holds until retracted; an unknown id is never silently dropped.
        return source_id not in self.retracted

    # ------------------------------------------------------------ queries

    @property
    def conflicts(self) -> ConflictScan:
        """Live declared checks; no checker means unchecked, never proven consistent."""
        from hypomnesis.epistemics.conflicts import ConflictChecker, ConflictScan

        if self.conflict_checker is None:
            return ConflictScan()
        if not isinstance(self.conflict_checker, ConflictChecker):
            raise ValueError("a conflict checker must be a ConflictChecker")
        return self.conflict_checker.scan(self)

    def value(self, key: str) -> Any:
        return self.facts[key].value

    def support(self, key: str) -> Support:
        return evaluate(
            self.facts[key].provenance,
            SUPPORT,
            lambda s: self.sources[s].support if self._holds(s) else Support.UNSUPPORTED,
        )

    def confidence(self, key: str) -> float:
        return evaluate(
            self.facts[key].provenance,
            CONFIDENCE,
            lambda s: self.sources[s].confidence if self._holds(s) else 0.0,
        )

    def sources_of(self, key: str) -> list[Source]:
        ids = dict.fromkeys(self.facts[key].provenance.observations())
        return [self.sources[i] for i in ids]

    def graph(self, *, detailed: bool = True) -> nx.DiGraph[str]:
        """The dependency graph, built on demand from ``sources``, ``facts`` and provenance.

        Nodes are ``fact:<key>`` and ``source:<id>`` (a hand-built provenance may still
        mention an undeclared source, flagged ``declared=False``). Edges go from a
        source to every fact
        whose provenance mentions it, and from a premise to its conclusion
        (``kind`` is ``"provenance"`` or ``"premise"``). With ``detailed`` the nodes
        carry value, method, support and confidence, ready for export.
        """
        g: nx.DiGraph[str] = nx.DiGraph()
        for source in self.sources.values():
            g.add_node(SOURCE + source.id, kind="source")
            if detailed:
                g.nodes[SOURCE + source.id].update(
                    origin=source.origin,
                    source_kind=source.kind,
                    support=source.support.label,
                    confidence=source.confidence,
                    retracted=source.id in self.retracted,
                )
        for key, fact in self.facts.items():
            g.add_node(FACT + key, kind="fact")
            if detailed:
                g.nodes[FACT + key].update(
                    value=fact.value,
                    method=fact.method,
                    support=self.support(key).label,
                    confidence=round(self.confidence(key), 3),
                )
            for source_id in dict.fromkeys(fact.provenance.observations()):
                if SOURCE + source_id not in g:
                    g.add_node(SOURCE + source_id, kind="source")
                    if detailed:
                        g.nodes[SOURCE + source_id].update(declared=False)
                g.add_edge(SOURCE + source_id, FACT + key, kind="provenance")
            for premise in fact.premises:
                if premise in self.facts:
                    g.add_edge(FACT + premise, FACT + key, kind="premise")
        return g

    def provenance_graph(self) -> dict[str, Any]:
        """The graph as node-link JSON data (reload with ``nx.node_link_graph``)."""
        return nx.node_link_data(self.graph(), edges="edges")

    def explain(self, key: str, depth: int = 0) -> list[str]:
        """Why a fact holds, from its provenance: one line per fact, premises indented."""
        graph = self.graph(detailed=False)
        if FACT + key not in graph:
            raise KeyError(key)
        return self._explain(graph, key, depth, ())

    def _explain(
        self, graph: nx.DiGraph[str], key: str, depth: int, path: tuple[str, ...]
    ) -> list[str]:
        if key in path:
            raise ValueError(f"cycle de prémisses : {' ← '.join((*path, key))}")
        fact = self.facts[key]
        lines = [
            f"{'  ' * depth}- {key} = {fact.value!r} : {fact.method} "
            f"[support {self.support(key).label}, confiance {self.confidence(key):.2f}]"
        ]
        for node in graph.predecessors(FACT + key):
            if graph.edges[node, FACT + key]["kind"] == "premise":
                lines.extend(self._explain(graph, node.removeprefix(FACT), depth + 1, (*path, key)))
        return lines

    def by_support(self, predicate: Callable[[Support], bool]) -> list[str]:
        return [k for k in self.facts if predicate(self.support(k))]
