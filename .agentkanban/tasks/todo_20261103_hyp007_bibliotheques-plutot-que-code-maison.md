---
title: "HYP-007 · TODO"
lane: todo
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T15:00:00+01:00
description: "Checklist de coordination de HYP-007 (lot 0, ordre des lots, clôture)"
---

# Iteration 1

Rôle : ticket de coordination des sept migrations (HYP-006, 008, 009, 014, 015, 016, 017). Il porte le **Lot 0** (dépendances, seul à toucher `pyproject.toml`) et la clôture. Sans GPU.

État des lieux : `pyproject.toml` ne déclare aujourd'hui que `lark`, `jsonschema[format-nongpl]`, `referencing`, `z3-solver` ; extra `llm` = `jinja2`, `scikit-learn` ; extra `dev` = idem + `pytest`, `hypothesis`, `ruff`, `pyright`, `pre-commit`. `.venv` contient PyYAML 6.0.3 (via pre-commit) mais ni typer, rich, networkx, ollama, opentelemetry, matplotlib.

Ordre et lots (fichiers disjoints au sein d'un lot) :
- Lot 0 : dépendances (ce ticket).
- Lot A (parallèle) : HYP-017 (`certify/load.py`), HYP-009 (`scripts/kanban.py`, `validate.sh`, `.pre-commit-config.yaml`), HYP-014 (`llm/ollama.py`).
- Lot B (parallèle, après le Lot 0) : HYP-006 (`cli.py`), HYP-008 (`epistemics/knowledge.py`, `engine/procedure.py` pour l'export du graphe), HYP-015 (`observability/trace.py`, façade, `procedure.py` intact). Les lots A et B peuvent aussi tourner ensemble : aucun fichier commun.
- Lot C (après HYP-006) : HYP-016 (`llm/plots.py` peut être écrit plus tôt ; seule l'option CLI attend).
- Clôture : HYP-007.

Règles pour travailler à plusieurs dans le même arbre : chaque ticket ne `git add` que **ses** fichiers ; `validate.sh rapide` peut échouer à cause du travail en cours d'un autre ticket (utiliser `pytest <ses tests>` et `ruff check <ses fichiers>` entre-temps) ; `complet` se lance une fois par lot, arbre stable ; `TECHNICAL.md` : chaque ticket ne modifie que sa propre ligne ou section. `ruff` interdit `noqa` et `type: ignore`.

- [ ] `pyproject.toml`, dépendances d'exécution : `typer>=0.12` (apporte Click et Rich), `networkx>=3.2`, `opentelemetry-api>=1.25`, `opentelemetry-sdk>=1.25`
- [ ] `pyproject.toml`, extra `llm` : `ollama>=0.3`, `matplotlib>=3.8` (en plus de `jinja2`, `scikit-learn`)
- [ ] `pyproject.toml`, extra `dev` : reprendre `llm` + `pyyaml>=6` (scripts/kanban.py), éventuellement `types-networkx` si Pyright se plaint (jamais `type: ignore`)
- [ ] `pip install -e '.[dev]'` dans `.venv` ; noter les versions installées dans la fiche ; vérifier `import typer, networkx, ollama, opentelemetry.sdk.trace, matplotlib, yaml`
- [ ] Vérifier que `.github/workflows/ci.yml` (`pip install -e '.[dev]'`) suffit ; sinon l'adapter
- [ ] `./scripts/validate.sh rapide` vert avant de lancer les lots ; commit « Dépendances des migrations vers bibliothèques » en français
- [ ] Après chaque lot : mettre à jour la colonne « Remplacement » du tableau de la fiche HYP-007 (fait / reste), relire `git status` pour détecter un fichier modifié par deux tickets
- [ ] Clôture : tous les tickets en `qa` ; `./scripts/validate.sh complet` vert sur l'arbre final ; `memory.md` (Outils, Conventions) à jour ; mettre HYP-007 en `qa`
