---
title: "HYP-007 · Remplacer le code maison par des bibliothèques courantes"
lane: todo
created: 2026-11-03T21:29:19+01:00
updated: 2026-11-04T08:55:00+01:00
description: "P1 · S · Fondations et gouvernance · coordination des migrations vers des bibliothèques"
---

## Conversation

### user

**Ticket** HYP-007 · **Priorité** P1 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-006, HYP-008, HYP-009, HYP-014, HYP-015, HYP-016, HYP-017 · **Labels** python, dette, coordination

#### Contexte

Préférence de l'utilisateur, notée dans `memory.md` : utiliser les bibliothèques courantes (NetworkX, NumPy, SciPy, scikit-learn, matplotlib, Typer, clients officiels, OpenTelemetry…) plutôt que du code maison, tant qu'elles restent raisonnables en poids. Seul ce qui est propre à Hypomnesis (langage, typage, IR, sémantique) est écrit à la main ; le noyau Lean reste sans dépendance.

Relevé des endroits concernés :

| Code maison | Remplacement | Fichiers |
|---|---|---|
| graphe de dépendances des faits (prémisses, invalidation en cascade, explication) | **NetworkX** `DiGraph` : `descendants` pour l'invalidation, parcours pour l'explication, export du graphe de provenance | `src/hypomnesis/epistemics/knowledge.py` |
| graphe des tâches du Kanban, détection de cycles, tâches prêtes | **NetworkX** : `simple_cycles`, `topological_generations`, chemin critique | `scripts/kanban.py` |
| client HTTP Ollama écrit avec `urllib` | client officiel **`ollama`** (Python) | `src/hypomnesis/llm/ollama.py` |
| traceur de spans maison | **OpenTelemetry SDK** (exportateur en mémoire pour les rapports, OTLP ensuite ; recoupe HYP-070) | `src/hypomnesis/observability/trace.py` |
| accesseurs de validation des certificats | **jsonschema**, avec le schéma déjà publié | `src/hypomnesis/certify/load.py` |
| CLI `argparse` | **Typer** (ticket dédié HYP-006) | `src/hypomnesis/cli.py` |
| tableaux du banc LLM en texte | **matplotlib** pour les graphiques (exactitude, latence, jetons par modèle) | `src/hypomnesis/llm/benchmark.py` |
| estimateurs par règles | **scikit-learn** quand un vrai modèle appris est voulu (ticket HYP-054) | langages M2 |

#### Découpage

Ce ticket coordonne les migrations ; chacune a son ticket, et celui-ci se termine quand elles le sont :

| Ticket | Migration |
|---|---|
| HYP-006 | CLI : argparse → Typer |
| HYP-008 | graphe de provenance des faits → NetworkX |
| HYP-009 | outil Kanban → NetworkX et PyYAML |
| HYP-014 | client LLM → paquet officiel `ollama` |
| HYP-015 | traceur maison → SDK OpenTelemetry (puis HYP-070) |
| HYP-016 | graphiques du banc LLM → matplotlib |
| HYP-017 | validation des certificats → `jsonschema` (déjà une dépendance) |
| HYP-054 | estimateurs appris → scikit-learn (ticket existant) |

#### Tâches proposées

- Après les migrations : relire `pyproject.toml` (une ligne de justification par dépendance ajoutée) et `TECHNICAL.md`.
- Vérifier qu'aucun autre code d'infrastructure maison ne subsiste ; ouvrir un ticket pour chaque cas trouvé.

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

### agent

**Point d'étape (2026-11-04 14:40).** Lot 0 fait (commit eaa6e55) : dépendances déclarées dans `pyproject.toml`.

| Ticket | Migration | État |
|---|---|---|
| HYP-006 | CLI : argparse → Typer | qa |
| HYP-008 | graphe de provenance → NetworkX | qa |
| HYP-009 | outil Kanban → NetworkX et PyYAML | qa |
| HYP-015 | traceur → SDK OpenTelemetry (façade `Tracer`) | qa |
| HYP-017 | certificats → `jsonschema` | qa |
| HYP-014 | client LLM → paquet `ollama` | doing (reste la validation finale) |
| HYP-016 | graphiques du banc → matplotlib | todo, en cours chez un implémenteur |
| HYP-054 | estimateurs appris → scikit-learn | bloqué (attend HYP-044, HYP-032), hors du périmètre de clôture |

Bug découvert pendant HYP-008 : HYP-143 (fait sans source déclarée `axiome`).

Pour la clôture, l'inventaire du code maison encore présent (avec bibliothèque candidate ou raison de le garder) est dans la checklist `todo_20261103_hyp007_…`, itération 2. Résumé : aucune autre migration ne s'impose ; trois examens restent ouverts (intervalles de confiance du banc avec `scipy.stats`, collecte des commentaires de doc par les callbacks du lexeur Lark, bibliothèque d'automate ou de relance pour HYP-061) et sont rattachés à leurs tickets plutôt qu'à un nouveau ticket.

### user

