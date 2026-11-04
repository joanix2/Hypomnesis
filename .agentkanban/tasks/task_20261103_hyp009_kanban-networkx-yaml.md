---
title: "HYP-009 · Outil Kanban : NetworkX pour les dépendances, PyYAML pour le front-matter"
lane: todo
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P2 · S · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-009 · **Priorité** P2 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, networkx, kanban, dette

#### Contexte

`scripts/kanban.py` détecte les cycles par un parcours écrit à la main et analyse le front-matter YAML ligne par ligne. Il était limité à la bibliothèque standard pour tourner dans des hooks git, qui ont été retirés : il est désormais lancé par `./scripts/validate.sh` avec l'environnement du projet.

#### Tâches proposées

- Graphe des tâches en `networkx.DiGraph` : cycles par `nx.simple_cycles`, ordre par `nx.topological_generations`.
- Ajouter à `status` le **chemin critique** (plus long chemin de dépendances vers les tâches P0 restantes).
- Front-matter avec `yaml.safe_load` (PyYAML), en tolérant les valeurs écrites par l'extension Agent Kanban.
- Lancer le script avec `.venv/bin/python` dans `validate.sh` (il ne dépend plus seulement de la bibliothèque standard).

#### Critères d'acceptation

- `check`, `status` et `graph` donnent les mêmes résultats qu'avant sur le Kanban actuel.
- `status` affiche le chemin critique.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `scripts/kanban.py`
- `scripts/validate.sh`
- `tests/tools/test_kanban.py`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)
