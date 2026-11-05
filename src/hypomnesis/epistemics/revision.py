"""Incremental retraction and full reference recomputation (HYP-033).

The index is derived from immutable provenance snapshots, not premise keys:
an old conclusion keeps its original sources after a premise is replaced.
Building the index reads metadata; only candidates are evaluated incrementally.
"""

from __future__ import annotations

from collections.abc import Mapping, Set
from typing import TYPE_CHECKING

from hypomnesis.epistemics.provenance import BOOLEAN, Plus, Prov, Times, Zero, evaluate

if TYPE_CHECKING:
    from hypomnesis.epistemics.knowledge import Fact


def dependency_index(facts: Mapping[str, Fact]) -> dict[str, frozenset[str]]:
    index: dict[str, set[str]] = {}
    for key, fact in facts.items():
        for source in fact.provenance.observations():
            index.setdefault(source, set()).add(key)
    return {source: frozenset(keys) for source, keys in index.items()}


def contains_zero(term: Prov) -> bool:
    if isinstance(term, Zero):
        return True
    if isinstance(term, Plus | Times):
        return contains_zero(term.left) or contains_zero(term.right)
    return False


def invalidated(facts: Mapping[str, Fact], retracted: Set[str]) -> list[str]:
    """Evaluate indexed or zero-bearing candidates, in fact insertion order."""
    index = dependency_index(facts)
    candidates = set().union(*(index.get(source, frozenset()) for source in retracted))
    candidates.update(key for key, fact in facts.items() if contains_zero(fact.provenance))
    return [
        key
        for key, fact in facts.items()
        if key in candidates
        and not evaluate(fact.provenance, BOOLEAN, lambda source: source not in retracted)
    ]


def recompute(facts: Mapping[str, Fact], retracted: Set[str]) -> dict[str, Fact]:
    """Full reference evaluation; it does not execute rules or invent missing values."""
    return {
        key: fact
        for key, fact in facts.items()
        if evaluate(fact.provenance, BOOLEAN, lambda source: source not in retracted)
    }
