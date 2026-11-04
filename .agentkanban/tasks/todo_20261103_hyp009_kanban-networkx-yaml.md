---
title: "HYP-009 · TODO"
lane: todo
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T15:00:00+01:00
description: "Checklist de HYP-009"
---

# Iteration 1

État des lieux (vérifié) : `scripts/kanban.py` n'importe que la bibliothèque standard. Il a un `_front_matter` et un `_unquote` écrits à la main (L78-100), `cycles()` par parcours récursif (L201-219), `blockers`/`is_ready`/`unblocks` (L221-235) et `status`/`_print_status` (L406-445) sans chemin critique. `tests/tools/test_kanban.py` protège `check`, `status`, `graph` (cycles, dépendances `qa`/`done`, format, injection idempotente). `PyYAML` 6.0.3 est présent dans `.venv` (via pre-commit) mais **non déclaré** ; NetworkX non installé. Le hook pre-commit `kanban-check` appelle `python3 scripts/kanban.py check` (Python système) et le Kanban est aussi lancé par `validate.sh` avec `$PY`.

Fichiers (disjoints des autres migrations) : `scripts/kanban.py`, `tests/tools/test_kanban.py`, `scripts/validate.sh`, `.pre-commit-config.yaml` (entrée du hook `kanban-check`). Ne PAS toucher `pyproject.toml` (Lot 0). Pas de GPU.

Risque : le front-matter écrit par l'extension Agent Kanban n'est pas toujours du YAML strict (guillemets, `:` dans les titres, dates). `yaml.safe_load` peut transformer `created:` en `datetime` ou refuser un fichier que le lecteur actuel accepte.

- [ ] Instantané avant migration : enregistrer la sortie de `check`, `status --json` et `graph` sur le Kanban actuel (fichier temporaire hors dépôt) pour la comparaison finale
- [ ] Test de caractérisation : charger tous les fichiers de `.agentkanban/tasks/` avec l'ancien et le nouveau lecteur de front-matter et comparer `title`, `lane`, `description` (les dates peuvent rester des chaînes)
- [ ] Front-matter : `yaml.safe_load` ; convertir les valeurs en `str` là où `Task` les attend ; garder les messages d'erreur « front-matter absent » et couloir inconnu
- [ ] Graphe des tâches en `networkx.DiGraph` (arête tâche → dépendance) ; `cycles` via `nx.simple_cycles` en gardant le texte « cycle de dépendances : A → B → A » (test `test_cycle_is_reported`)
- [ ] `blockers`, `is_ready`, `unblocks` : lire les prédécesseurs/successeurs du graphe ; mêmes résultats
- [ ] Ordre d'affichage par `nx.topological_generations` quand utile, en conservant le tri priorité puis identifiant de `_sort_key`
- [ ] `status` : ajouter le **chemin critique** (plus long chemin de dépendances vers les tâches P0 restantes : `nx.dag_longest_path` sur le sous-graphe) en texte et dans `--json` ; test dédié sur un petit tableau
- [ ] Mettre à jour la docstring du script (« bibliothèque standard uniquement » devient faux) et `memory.md` (« Outils »)
- [ ] `validate.sh` : exécuter `kanban.py` avec `"$PY"` (déjà le cas, vérifier) ; `.pre-commit-config.yaml` : entrée du hook au même modèle que Ruff/Pyright (`PY=.venv/bin/python; …`) au lieu de `python3`
- [ ] Comparer `check`/`status`/`graph` avant et après : identiques (hors chemin critique)
- [ ] `python3 scripts/kanban.py check` reste vert sur tout le tableau (les tâches en cours d'écriture par les autres lots incluses)
- [ ] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
