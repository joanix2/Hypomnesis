"""Characterisation of revision and explanation on the M1 programs, and of the M0 export.

The expectations below were recorded before the provenance graph replaced the
hand-written premise walks: they must not change with the graph.
"""

import json
from pathlib import Path

import networkx as nx

from hypomnesis.engine.language import load_language
from hypomnesis.engine.procedure import run_procedure

ROOT = Path(__file__).resolve().parents[2]
MESUREE = (ROOT / "demo" / "programs" / "mecanique" / "plaque_mesuree.hyp").read_text()
PLAQUE = (ROOT / "demo" / "programs" / "mecanique" / "plaque_120x80.hyp").read_text()
SALLE = (ROOT / "demo" / "programs" / "ventilation" / "salle_serveurs.hyp").read_text()

OBSERVED = "[support observé, confiance 1.00]"
DEMANDE = "observé (programme M1 : demande)"


def measured(tmp_path):
    return run_procedure(
        load_language(ROOT / "demo" / "languages" / "mecanique"),
        MESUREE,
        out_dir=tmp_path,
        environment={"mesure": "5"},
    )


def broken_fan(tmp_path):
    return run_procedure(
        load_language(ROOT / "demo" / "languages" / "ventilation"),
        SALLE,
        mode="production",
        environment={"panne": "1"},
        out_dir=tmp_path,
    )


def invalidated(kb):
    return [e.key for e in kb.journal if e.kind == "invalidated"]


def test_measurement_invalidates_the_estimate_and_its_conclusions_in_order(tmp_path):
    kb = measured(tmp_path).kb
    assert invalidated(kb) == [
        "epaisseur.estimation",
        "demande.epaisseur",
        "demande.masse_kg",
        "demande.valide",
    ]
    assert [(e.seq, e.kind, e.key) for e in kb.journal[9:14]] == [
        (10, "retracted", "est-5"),
        (11, "invalidated", "epaisseur.estimation"),
        (12, "invalidated", "demande.epaisseur"),
        (13, "invalidated", "demande.masse_kg"),
        (14, "invalidated", "demande.valide"),
    ]
    assert len(kb.journal) == 17
    assert list(kb.facts) == [
        "demande.nom",
        "demande.largeur",
        "demande.hauteur",
        "demande.masse_max",
        "pied-a-coulisse#1",
        "demande.epaisseur",
        "demande.masse_kg",
        "demande.valide",
    ]


def test_explanation_after_measurement_is_unchanged(tmp_path):
    kb = measured(tmp_path).kb
    sensor = (
        "pied-a-coulisse#1 = {'sensor_id': 'pied-a-coulisse', 'thickness_mm': 5.0} "
        f": observé (capteur pied-a-coulisse) {OBSERVED}"
    )
    assert kb.explain("demande.valide") == [
        f"- demande.valide = True : Plaque.verifier {OBSERVED}",
        f"  - demande.epaisseur = 5.0 : mesure directe {OBSERVED}",
        f"    - {sensor}",
        f"  - demande.nom = 'plaque-mesuree' : {DEMANDE} {OBSERVED}",
        f"  - demande.largeur = 120.0 : {DEMANDE} {OBSERVED}",
        f"  - demande.hauteur = 80.0 : {DEMANDE} {OBSERVED}",
        f"  - demande.masse_max = 0.5 : {DEMANDE} {OBSERVED}",
    ]


def test_refuted_hypothesis_invalidates_its_dependants_in_order(tmp_path):
    kb = broken_fan(tmp_path).kb
    assert [(e.seq, e.kind, e.key) for e in kb.journal[5:9]] == [
        (6, "retracted", "hyp-1"),
        (7, "invalidated", "hypothese"),
        (8, "invalidated", "effet_attendu.1"),
        (9, "derived", "hypothese.refutee"),
    ]
    assert list(kb.facts) == ["thermo-1#1", "decision.1", "thermo-1#2", "hypothese.refutee"]
    thermo = "{'sensor_id': 'thermo-1', 'celsius': %s} : observé (capteur thermo-1)"
    assert kb.explain("hypothese.refutee") == [
        "- hypothese.refutee = True : commande exécutée mais température non abaissée " + OBSERVED,
        f"  - decision.1 = 100 : Ventilation.decider {OBSERVED}",
        f"    - thermo-1#1 = {thermo % 31.0} {OBSERVED}",
        f"  - thermo-1#1 = {thermo % 31.0} {OBSERVED}",
        f"  - thermo-1#2 = {thermo % 31.2} {OBSERVED}",
    ]


def test_m0_report_contains_the_provenance_graph(tmp_path):
    report = run_procedure(
        load_language(ROOT / "demo" / "languages" / "mecanique"), PLAQUE, out_dir=tmp_path
    )
    data = json.loads(json.dumps(report.to_json()))["provenance_graph"]
    graph = nx.node_link_graph(data, edges="edges")
    facts = {n for n, d in graph.nodes(data=True) if d["kind"] == "fact"}
    assert facts == {f"fact:{key}" for key in report.kb.facts}
    assert graph.has_edge("fact:demande.epaisseur", "fact:demande.masse_kg")
    estimate = next(s.id for s in report.kb.sources.values() if s.kind == "estimation")
    assert graph.has_edge(f"source:{estimate}", "fact:demande.epaisseur")
    assert graph.nodes["fact:demande.valide"]["support"] == "estimé"
    assert nx.is_directed_acyclic_graph(graph)
