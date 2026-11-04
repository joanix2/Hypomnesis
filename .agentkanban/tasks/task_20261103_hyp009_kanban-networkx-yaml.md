---
title: "HYP-009 · Outil Kanban : NetworkX pour les dépendances, PyYAML pour le front-matter"
lane: qa
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P2 · S · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
priority: P2
tags: [dette, kanban, networkx, outillage, python]
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

### agent

HYP-009 implémenté (commit `1ba0c57`).

- **Front-matter** : `yaml.load` avec un `SafeLoader` dérivé dont le résolveur de timestamps est retiré (les dates restent des chaînes telles qu'écrites par l'extension ; `yaml.safe_load` brut les aurait converties en `datetime`). Un YAML invalide produit « front-matter invalide (…) » ; « front-matter absent » est conservé.
- **Graphe** : `dependency_graph()` renvoie un `nx.DiGraph` tâche → dépendance ; `cycles` via `nx.simple_cycles` (message identique, rotation canonique au plus petit identifiant) ; `blockers`, `is_ready`, `unblocks` lisent le graphe.
- **status** : nouvelle clé `critical_path` (JSON) et section « Chemin critique vers P0 » (texte) : plus longue chaîne de tâches non terminées (`nx.dag_longest_path`) vers une tâche P0 restante, rendue dépendance d'abord. Actuellement : HYP-040 → 041 → 042 → 044 → 052 → 055 → 090.
- **Non-régression** : instantané avant/après sur les 96 fiches : `check` identique, `status` identique hors section chemin critique, `status --json` identique hors `critical_path`, tâches parsées et nœuds/relations injectés pour Graphify identiques (comparaison de l'ancien module avec le nouveau).
- Tests ajoutés (`tests/tools/test_kanban.py`) : cycle, front-matter (guillemets, `:`, dates), invalide/absent, chemin critique (avec et sans P0). `.pre-commit-config.yaml` : hook `kanban-check` lancé avec `.venv`. `TECHNICAL.md` et `memory.md` mis à jour. `validate.sh` utilisait déjà `"$PY"`.

**Écarts** : `nx.topological_generations` non utilisé (le tri priorité puis identifiant est conservé, aucun besoin d'ordre topologique à l'affichage). Les dépendances en double dans une fiche sont désormais dédoublonnées (effet du graphe) ; aucun cas sur le tableau actuel. Test de caractérisation : fait par comparaison ponctuelle ancien/nouveau lecteur, non conservé comme test (l'ancien lecteur n'existe plus).

**Vigilance** : `validate.sh complet` a échoué une première fois à cause du travail en cours d'autres agents (`cli.py` importait `click`, absent à ce moment) ; relancés ensuite, pre-commit (kanban compris) et la suite de tests (tous verts) passent. Étape Lean verte. Pyright ne couvre que `src` ; `scripts/kanban.py` a une alerte préexistante (`__doc__` optionnel) hors périmètre.

### user
