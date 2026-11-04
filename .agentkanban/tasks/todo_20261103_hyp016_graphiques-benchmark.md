---
title: "HYP-016 · TODO"
lane: todo
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T15:00:00+01:00
description: "Checklist de HYP-016"
---

# Iteration 1

État des lieux (vérifié) : `llm/benchmark.py` (306 lignes) produit `summary(results) -> str` (tableau Markdown) ; `CaseResult` expose `label`, `parsed_first`, `typed_first`, `first_ok`, `split`, `translation` (tentatives). `cli.py::_benchmark` écrit `resultats-<horodatage>.json` (`r.to_json()`) et `resume-<horodatage>.md` dans `sortie/benchmark-llm/`. matplotlib n'est **pas** installé. Aucun chargeur de résultats JSON n'existe : le critère « un lot JSON existant suffit à régénérer les figures » impose d'en écrire un côté `llm/`.

Fichiers : `src/hypomnesis/llm/plots.py` (nouveau, **aucun conflit**), `tests/unit/test_plots.py` (nouveau), puis `src/hypomnesis/cli.py` (option de `benchmark-llm`). **L'étape CLI se fait après HYP-006** (Typer réécrit tout `cli.py`). Ne PAS toucher `pyproject.toml` (Lot 0 : `matplotlib` dans le groupe `llm` et `dev`). Pas de GPU : les tests utilisent des résultats synthétiques ou un `resultats-*.json` déjà présent dans `sortie/` si le dossier existe.

- [ ] Relire `CaseResult.to_json()` et fixer le schéma des résultats ; ajouter `load_results(path) -> list[dict]` avec validation minimale des clés utilisées par les figures
- [ ] Données pures : fonctions sans matplotlib qui calculent les séries (exactitude par niveau — parsé, typé, correct, exécuté — par modèle ; latence et jetons générés par modèle ; réussite par cas) ; testées directement
- [ ] `plots.py` : backend `Agg` fixé avant l'import de `pyplot`, une fonction par figure, retourne la `Figure`, écrit PNG et SVG
- [ ] `render_all(results, directory)` : écrit les figures à côté du résumé dans `sortie/benchmark-llm/`
- [ ] Tests : les fichiers PNG et SVG sont créés, non vides ; le SVG contient les libellés de modèles ; aucune fenêtre ouverte
- [ ] **Après HYP-006** — CLI : `hypomnesis benchmark-llm --graphiques resultats.json` régénère les figures sans relancer le banc (sans appeler Ollama) ; `--sans-graphiques` désactive les figures lors d'un run
- [ ] Test CLI : `main(["benchmark-llm", "--graphiques", fichier, "--sortie", tmp])` retourne 0 et crée les figures
- [ ] `TECHNICAL.md` : section Banc LLM (figures)
- [ ] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
