---
title: "HYP-007 · Remplacer le code maison par des bibliothèques courantes"
lane: todo
created: 2026-11-03T21:29:19+01:00
updated: 2026-11-03T21:29:19+01:00
description: "P1 · M · Fondations et gouvernance · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-007 · **Priorité** P1 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, dette

#### Contexte

Préférence de l'utilisateur, notée dans `memory.md` : utiliser les bibliothèques courantes (NetworkX, NumPy, SciPy, scikit-learn, matplotlib, Typer, clients officiels, OpenTelemetry…) plutôt que du code maison, tant qu'elles restent raisonnables en poids. Seul ce qui est propre à Hypomnesis (langage, typage, IR, sémantique) est écrit à la main ; le noyau Lean reste sans dépendance.

Relevé des endroits concernés :

| Code maison | Remplacement | Fichiers |
|---|---|---|
| graphe de dépendances des faits (prémisses, invalidation en cascade, explication) | **NetworkX** `DiGraph` : `descendants` pour l'invalidation, parcours pour l'explication, export du graphe de provenance | `src/hypomnesis/epistemics/knowledge.py` |
| graphe des tâches du Kanban, détection de cycles, tâches prêtes | **NetworkX** : `simple_cycles`, `topological_generations`, chemin critique | `scripts/kanban.py` |
| client HTTP Ollama écrit avec `urllib` | client officiel **`ollama`** (Python) | `src/hypomnesis/llm/ollama.py` |
| traceur de spans maison | **OpenTelemetry SDK** (exportateur en mémoire pour les rapports, OTLP ensuite ; recoupe HYP-070) | `src/hypomnesis/observability/trace.py` |
| CLI `argparse` | **Typer** (ticket dédié HYP-006) | `src/hypomnesis/cli.py` |
| tableaux du banc LLM en texte | **matplotlib** pour les graphiques (exactitude, latence, jetons par modèle) | `src/hypomnesis/llm/benchmark.py` |
| estimateurs par règles | **scikit-learn** quand un vrai modèle appris est voulu (ticket HYP-054) | langages M2 |

#### Tâches proposées

- Ajouter les dépendances retenues à `pyproject.toml`, avec une justification d'une ligne chacune.
- Remplacer chaque élément du tableau, sans changer le comportement observable : mêmes API publiques, mêmes rapports.
- Supprimer le code maison devenu inutile.
- Mettre à jour `TECHNICAL.md`.

#### Critères d'acceptation

- Tous les tests existants passent sans modification de leurs attentes.
- Les propriétés de la provenance (tests `tests/property/`, miroirs des théorèmes Lean) restent vraies.
- Le test d'architecture (aucun domaine dans le moteur) passe toujours.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/epistemics/knowledge.py`, `src/hypomnesis/llm/ollama.py`, `src/hypomnesis/observability/trace.py`, `src/hypomnesis/llm/benchmark.py`
- `scripts/kanban.py`, `pyproject.toml`, `TECHNICAL.md`

#### Références

- `.agentkanban/memory.md` (préférence « bibliothèques plutôt que code maison »)
- Tickets liés : HYP-006 (Typer), HYP-054 (scikit-learn), HYP-070 (OpenTelemetry)

