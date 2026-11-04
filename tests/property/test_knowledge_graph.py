"""The provenance graph agrees with the Boolean evaluation of provenance (P10, P11).

Graph descendants are only the *candidate* set of a revision; the Boolean
semiring decides. On bases built by ``derive`` (products only) both coincide;
with alternative derivations (``plus``) the candidates strictly over-approximate.
"""

import networkx as nx
from hypothesis import given, settings
from hypothesis import strategies as st

from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.provenance import BOOLEAN, evaluate

# One step builds one fresh fact: a direct record, or a derivation from a subset of
# earlier facts (picked by index modulo their number; empty = an axiom).
steps = st.tuples(
    st.sampled_from(["observe", "estimate", "hypothesis", "derive", "derive"]),
    st.lists(st.integers(min_value=0, max_value=1000), max_size=4),
)


def build(plan, *, axioms: bool) -> KnowledgeBase:
    kb = KnowledgeBase()
    for i, (kind, picks) in enumerate(plan):
        key = f"f{i}"
        if kind == "observe":
            kb.observe(key, i, "capteur")
        elif kind == "estimate":
            kb.estimate(key, i, "modèle", 0.5)
        elif kind == "hypothesis":
            kb.hypothesis(key, i, "hypothèse", 0.5)
        elif i or axioms:
            existing = list(kb.facts)
            premises = (
                list(dict.fromkeys(existing[p % len(existing)] for p in picks)) if existing else []
            )
            if premises or axioms:
                kb.derive(key, i, "règle", premises)
    return kb


def reference_invalidated(kb: KnowledgeBase, source_id: str) -> list[str]:
    """What the pre-graph implementation did: evaluate every fact without the source."""
    return [
        key
        for key, fact in kb.facts.items()
        if not evaluate(fact.provenance, BOOLEAN, lambda s: s != source_id and s in kb.sources)
    ]


@settings(max_examples=100, deadline=None)
@given(st.lists(steps, min_size=1, max_size=14), st.data())
def test_revision_equals_boolean_evaluation_of_every_fact(plan, data):
    kb = build(plan, axioms=True)
    sources = sorted(kb.sources)
    if not sources:
        return
    source = data.draw(st.sampled_from(sources))
    expected = reference_invalidated(kb, source)
    assert kb.retract_source(source, "test") == expected
    for fact in kb.facts.values():  # P10/P11: what is left still holds without the source
        assert evaluate(fact.provenance, BOOLEAN, lambda s: s != source and s in kb.sources)


@settings(max_examples=100, deadline=None)
@given(st.lists(steps, min_size=1, max_size=14), st.data())
def test_descendants_of_the_source_are_exactly_the_invalidated_facts(plan, data):
    kb = build(plan, axioms=False)
    sources = sorted(kb.sources)
    if not sources:
        return
    source = data.draw(st.sampled_from(sources))
    graph = kb.graph(detailed=False)
    assert nx.is_directed_acyclic_graph(graph)  # fresh keys: no premise cycle
    candidates = {n for n in nx.descendants(graph, f"source:{source}") if n.startswith("fact:")}
    assert {f"fact:{k}" for k in kb.retract_source(source, "test")} == candidates


@settings(max_examples=100, deadline=None)
@given(st.lists(steps, min_size=1, max_size=10), st.data())
def test_alternative_derivations_make_the_graph_over_approximate(plan, data):
    kb = build(plan, axioms=False)
    sources = sorted(kb.sources)
    if len(kb.facts) < 2 or not sources:
        return
    # `alt` holds through either of two facts (plus): it survives losing one source.
    a, b = list(kb.facts)[:2]
    kb.facts["alt"] = Fact("alt", 0, kb.facts[a].provenance + kb.facts[b].provenance, "alt", (a, b))
    source = data.draw(st.sampled_from(sources))
    candidates = nx.descendants(kb.graph(detailed=False), f"source:{source}")
    expected = reference_invalidated(kb, source)
    assert kb.retract_source(source, "test") == expected
    assert {f"fact:{k}" for k in expected} <= candidates
