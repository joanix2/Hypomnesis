---
title: "HYP-008 · TODO"
lane: qa
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T18:19:29+01:00
description: "Checklist de HYP-008"
priority: P1
tags: [dette, epistemique, moteur-symbolique, networkx, python]
---

# Iteration 1

État des lieux (vérifié) : `epistemics/knowledge.py` porte `Source`, `Fact` (avec `provenance: Prov` et `premises`), `Unknown`, `Event` et `KnowledgeBase`. Le code maison : `retract_source` réévalue **chaque** fait avec `evaluate(fact.provenance, BOOLEAN, …)` (substitution `x ↦ 0`, propriétés P10/P11) ; `explain` récurse sur `fact.premises` ; il n'existe aucun graphe. Consommateurs : `engine/procedure.py` (`kb.facts`, `kb.retract_source`, `kb.source_id`, `kb.explain`, rapport M0 `to_json` vers L109-117) et `tests/integration/test_languages.py` (`kb.facts[...]`, révision par mesure). NetworkX n'est **pas** installé.

Décision de conception : les termes de provenance en semi-anneau (`provenance.py`) restent la **source de vérité** du support et de la confiance. NetworkX remplace les parcours de prémisses (invalidation candidate, explication) et sert d'export.

Risque : `descendants` d'une source sur-invalide un fait qui aurait deux dérivations (`Plus`) dont l'une survit. Aujourd'hui `derive` ne produit que des `Times`, donc les deux méthodes coïncident ; le test de propriétés doit le vérifier et l'invalidation finale doit rester décidée par l'évaluation booléenne (le graphe ne fournit que l'ensemble candidat).

Fichiers : `src/hypomnesis/epistemics/knowledge.py`, `src/hypomnesis/engine/procedure.py` (uniquement l'export du graphe dans le rapport), `tests/property/`, `tests/unit/`. **Ne pas** toucher `pyproject.toml` (Lot 0 de HYP-007) ni `observability/trace.py` (HYP-015 laisse `procedure.py` intact grâce à une façade `Tracer`).

- [x] Test de caractérisation avant tout changement : pour le scénario de révision par mesure et la réfutation d'hypothèse, enregistrer l'ensemble exact des clés invalidées, l'ordre du `journal` et la sortie de `explain` ; ces tests doivent rester verts après
- [x] `KnowledgeBase.graph()` : `nx.DiGraph` dont les nœuds sont les faits et les sources (attributs : valeur, support, confiance, méthode), arêtes source → fait et prémisse → conclusion ; construit à la demande à partir de `facts` et `sources`
- [x] `retract_source` : ensemble candidat = `nx.descendants` du nœud source ; invalidation confirmée par l'évaluation booléenne de la provenance (comportement actuel conservé) ; journal identique
- [x] `explain` : parcours du graphe (arbre des prémisses) en gardant exactement le rendu texte actuel
- [x] Export du graphe en JSON node-link (`nx.node_link_data`) ; l'ajouter au rapport M0 dans `ProcedureReport.to_json` (clé `provenance_graph`)
- [x] Test Hypothesis (`tests/property/`) : sur des bases aléatoires de faits dérivés, `descendants(source)` ∩ faits = ensemble invalidé par l'évaluation booléenne ; vérifie P10/P11 côté Python
- [x] Test : le rapport M0 d'un run de la plaque contient `provenance_graph` avec les nœuds attendus ; l'export se recharge (`node_link_graph`)
- [x] Pyright en mode basic : annoter `nx.DiGraph[str]` si nécessaire ; pas de `type: ignore`
- [x] `TECHNICAL.md` : section Épistémique (graphe NetworkX, source de vérité = provenance)
- [x] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
