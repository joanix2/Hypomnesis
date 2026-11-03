---
id: HYP-031
title: "Provenance en semi-anneau (implémentation Python)"
status: backlog
priority: P0
size: M
epic: P2-EPISTEMIQUE
depends_on: [HYP-030]
labels: [python]
assignee: 
---

# HYP-031 — Provenance en semi-anneau (implémentation Python)

## Contexte

Formalisé et prouvé dans `formal/Hypomnesis/Epistemics/Provenance.lean` (P9–P13). Il faut l'implémentation Python correspondante, fidèle au modèle Lean.

## Tâches

- [ ] `epistemics/provenance.py` : termes `obs`, `zero`, `one`, `plus`, `times` ; évaluation dans un semi-anneau.
- [ ] Semi-anneaux : support (treillis), booléen, Viterbi (confiance), tropical (coût).
- [ ] Substitution et retrait (`retract`).
- [ ] Tests Hypothesis reproduisant les énoncés Lean : `eval_subst`, `holds_after_retract`, `retract_unrelated`, `support_mono`.

## Critères d'acceptation

- [ ] Les quatre propriétés sont testées sur des termes générés.
- [ ] La docstring cite le théorème Lean correspondant à chaque propriété.

## Fichiers concernés

- `src/hypomnesis/epistemics/provenance.py`
- `tests/property/`

## Références

- `formal/Hypomnesis/Epistemics/Provenance.lean`
- Conventions et définition de fini : `kanban/README.md`
