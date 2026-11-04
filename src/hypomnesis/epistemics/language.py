"""Host bridge to immutable Knowledge data; never performs observation or revision."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.provenance import Obs, One, Plus, Prov, Support, Times, Zero
from hypomnesis.runtime.json import data_to_json
from hypomnesis.runtime.values import RecordValue, Variant, from_iterable


def provenance_value(proof: Prov) -> Variant:
    if isinstance(proof, Zero):
        return Variant("Zero", None, 0)
    if isinstance(proof, One):
        return Variant("One", None, 1)
    if isinstance(proof, Obs):
        return Variant("Source", proof.id, 2)
    if isinstance(proof, Plus | Times):
        return Variant(
            "Plus" if isinstance(proof, Plus) else "Times",
            (provenance_value(proof.left), provenance_value(proof.right)),
            3 if isinstance(proof, Plus) else 4,
        )
    raise ValueError(f"unsupported provenance: {type(proof).__name__}")


def support_value(grade: Support) -> Variant:
    names = {
        Support.OBSERVED: "Observed",
        Support.ESTIMATED: "Estimated",
        Support.DEFAULTED: "Defaulted",
        Support.HYPOTHESIS: "Hypothesis",
        Support.UNSUPPORTED: "Unsupported",
    }
    return Variant(names[grade], None, int(grade))


def snapshot_value(
    base: KnowledgeBase, *, encode: Callable[[Fact], Any] = lambda fact: fact.value
) -> RecordValue:
    facts = [
        RecordValue(
            "Knowledge.fact",
            (
                ("key", fact.key),
                ("value", data_to_json(encode(fact))),
                ("provenance", provenance_value(fact.provenance)),
                ("method", fact.method),
                ("premises", from_iterable(fact.premises)),
            ),
        )
        for _, fact in sorted(base.facts.items())
    ]
    sources = [
        (identifier, support_value(source.support))
        for identifier, source in sorted(base.sources.items())
    ]
    return RecordValue(
        "Knowledge.t",
        (
            ("sources", from_iterable(sources)),
            ("facts", from_iterable(facts)),
            ("retracted", from_iterable(sorted(base.retracted))),
        ),
    )
