"""Knowledge base: the NetworkX provenance graph and its agreement with the semiring."""

import json

import networkx as nx
import pytest

from hypomnesis.epistemics.knowledge import Fact, KnowledgeBase
from hypomnesis.epistemics.provenance import Support, obs


def chain(depth: int) -> tuple[KnowledgeBase, str]:
    kb = KnowledgeBase()
    root = kb.estimate("f0", 0, "mesure", 0.9)
    for i in range(1, depth + 1):
        kb.derive(f"f{i}", i, "suite", [f"f{i - 1}"])
    return kb, kb.source_id(root.key)


def test_graph_links_sources_to_facts_and_premises_to_conclusions():
    kb = KnowledgeBase()
    kb.observe("a", 1, "capteur")
    kb.estimate("b", 2, "modèle", 0.5)
    kb.derive("c", 3, "somme", ["a", "b"])
    g = kb.graph()
    assert set(g.edges(data="kind")) == {
        ("source:obs-1", "fact:a", "provenance"),
        ("source:est-2", "fact:b", "provenance"),
        ("source:obs-1", "fact:c", "provenance"),
        ("source:est-2", "fact:c", "provenance"),
        ("fact:a", "fact:c", "premise"),
        ("fact:b", "fact:c", "premise"),
    }
    assert g.nodes["fact:c"]["support"] == "estimé"
    assert g.nodes["fact:c"]["confidence"] == 0.5
    assert g.nodes["source:est-2"]["origin"] == "modèle"
    assert nx.is_directed_acyclic_graph(g)


def test_deep_chain_is_invalidated_entirely_and_explained_in_order():
    kb, source = chain(60)
    assert kb.explain("f60")[0].startswith("- f60 = 60 : suite")
    lines = kb.explain("f60")
    assert [len(line) - len(line.lstrip()) for line in lines] == [2 * i for i in range(61)]
    assert [line.split()[1] for line in lines] == [f"f{60 - i}" for i in range(61)]
    assert kb.retract_source(source, "test") == [f"f{i}" for i in range(61)]
    assert not kb.facts


def test_fact_with_two_derivations_survives_when_one_source_is_retracted():
    kb = KnowledgeBase()
    kb.observe("a", 1, "capteur 1")
    kb.observe("b", 1, "capteur 2")
    kb.derive("c", 2, "doublon", ["a"])
    # A second, alternative derivation of the same conclusion (semiring `plus`).
    both = kb.facts["a"].provenance + kb.facts["b"].provenance
    kb.facts["d"] = Fact("d", 2, both, "alternative", ("a", "b"))
    graph = kb.graph(detailed=False)
    assert {"fact:c", "fact:d"} <= nx.descendants(graph, "source:obs-1")  # candidates
    assert kb.retract_source("obs-1", "panne") == ["a", "c"]  # d still has b
    assert "d" in kb.facts and "b" in kb.facts


def test_premise_less_fact_is_not_invalidated_by_an_unrelated_retraction():
    kb = KnowledgeBase()
    kb.observe("a", 1, "capteur")
    kb.derive("axiome", True, "postulat", [])
    assert kb.retract_source("obs-1", "test") == ["a"]
    assert kb.value("axiome") is True


def test_premise_less_fact_has_a_readable_support_and_confidence():
    # HYP-143, symptom (a): the provenance used to mention an undeclared source.
    kb = KnowledgeBase()
    kb.derive("c.k", 1, "constante", [])
    assert kb.support("c.k") == Support.DEFAULTED
    assert kb.confidence("c.k") == 1.0
    assert [s.id for s in kb.sources_of("c.k")] == ["axiome"]
    assert kb.explain("c.k") == ["- c.k = 1 : constante [support par défaut, confiance 1.00]"]
    data = json.loads(json.dumps(kb.provenance_graph()))
    nodes = {n["id"]: n for n in data["nodes"]}
    assert nodes["fact:c.k"]["support"] == "par défaut"
    assert nodes["source:axiome"]["source_kind"] == "default"
    assert nodes["source:axiome"]["retracted"] is False


def test_premise_less_fact_survives_the_retraction_of_an_unrelated_source():
    # HYP-143, symptom (b): the first retraction used to invalidate it.
    kb = KnowledgeBase()
    kb.derive("c.k", 1, "constante", [])
    kb.observe("a", 1, "capteur")
    assert kb.retract_source("obs-1", "test") == ["a"]
    assert kb.value("c.k") == 1
    assert kb.support("c.k") == Support.DEFAULTED


def test_axiom_is_declared_once_and_never_retracted():
    kb = KnowledgeBase()
    kb.derive("c.k", 1, "constante", [])
    kb.derive("c.j", 2, "constante", [])
    assert list(kb.sources) == ["axiome"]
    with pytest.raises(ValueError, match="axiome"):
        kb.retract_source("axiome", "test")
    assert "axiome" not in kb.retracted
    assert set(kb.facts) == {"c.k", "c.j"}


def test_conclusion_from_an_axiom_and_an_observation_follows_the_observation():
    kb = KnowledgeBase()
    kb.derive("c.k", 2, "constante", [])
    kb.observe("a", 1, "capteur")
    kb.derive("d", 3, "produit", ["c.k", "a"])
    assert kb.support("d") == Support.DEFAULTED  # the weakest premise wins
    assert kb.retract_source("obs-1", "panne") == ["a", "d"]
    assert "c.k" in kb.facts


def test_retracting_an_unrelated_source_touches_nothing():
    kb = KnowledgeBase()
    kb.observe("a", 1, "capteur")
    kb.observe("b", 2, "capteur")
    kb.derive("c", 3, "somme", ["b"])
    assert kb.retract_source("obs-1", "test") == ["a"]
    assert list(kb.facts) == ["b", "c"]


def test_premise_replaced_by_a_new_source_keeps_provenance_semantics():
    kb = KnowledgeBase()
    kb.observe("a", 1, "premier capteur")
    kb.derive("b", 2, "double", ["a"])
    kb.observe("a", 5, "second capteur")  # `a` is replaced; `b` keeps the old provenance
    assert kb.retract_source("obs-2", "test") == ["a"]
    assert kb.retract_source("obs-1", "test") == ["b"]


def test_rederiving_from_a_conclusion_makes_a_premise_cycle_that_explain_rejects():
    kb = KnowledgeBase()
    kb.observe("a", 1, "capteur")
    kb.derive("b", 2, "suite", ["a"])
    kb.derive("a", 3, "retour", ["b"])  # the key `a` now depends on `b`, which depends on `a`
    assert not nx.is_directed_acyclic_graph(kb.graph())
    with pytest.raises(ValueError, match="cycle"):
        kb.explain("a")
    assert kb.retract_source("obs-1", "test") == ["a", "b"]  # revision still terminates


def test_explain_of_an_unknown_fact_raises():
    with pytest.raises(KeyError):
        KnowledgeBase().explain("absent")


def test_provenance_graph_is_json_and_reloads():
    kb = KnowledgeBase()
    kb.observe("a", {"x": [1, 2]}, "capteur")
    kb.derive("b", 1, "suite", ["a"])
    data = json.loads(json.dumps(kb.provenance_graph()))
    g = nx.node_link_graph(data, edges="edges")
    assert set(g) == set(kb.graph())
    assert g.nodes["fact:a"]["value"] == {"x": [1, 2]}
    assert g.has_edge("fact:a", "fact:b")


def test_axiom_source_is_declared_in_the_graph():
    kb = KnowledgeBase()
    kb.derive("axiome", True, "postulat", [])
    graph = kb.graph(detailed=False)
    assert graph.nodes["source:axiome"]["kind"] == "source"
    assert "declared" not in graph.nodes["source:axiome"]
    assert graph.has_edge("source:axiome", "fact:axiome")
    assert obs("axiome") == kb.facts["axiome"].provenance


def test_undeclared_sources_appear_as_such():
    kb = KnowledgeBase()
    kb.facts["x"] = Fact("x", 1, obs("fantome"), "à la main")
    graph = kb.graph(detailed=False)
    assert graph.nodes["source:fantome"]["kind"] == "source"
    assert kb.retract_source("autre", "test") == []  # an unknown source is not dropped
    assert "x" in kb.facts
