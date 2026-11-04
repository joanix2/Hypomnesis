---
title: "HYP-031 · Provenance en semi-anneau (implémentation Python)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 2 — Moteur épistémique · dépend de HYP-030"
priority: P0
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-031 · **Priorité** P0 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-030 · **Labels** python

#### Contexte

Formalisé et prouvé dans `formal/Hypomnesis/Epistemics/Provenance.lean` (P9–P13). Il faut l'implémentation Python correspondante, fidèle au modèle Lean.

#### Tâches proposées

- `epistemics/provenance.py` : termes `obs`, `zero`, `one`, `plus`, `times` ; évaluation dans un semi-anneau.
- Semi-anneaux : support (treillis), booléen, Viterbi (confiance), tropical (coût).
- Substitution et retrait (`retract`).
- Tests Hypothesis reproduisant les énoncés Lean : `eval_subst`, `holds_after_retract`, `retract_unrelated`, `support_mono`.

#### Critères d'acceptation

- Les quatre propriétés sont testées sur des termes générés.
- La docstring cite le théorème Lean correspondant à chaque propriété.

#### Fichiers concernés

- `src/hypomnesis/epistemics/provenance.py`
- `tests/property/`

#### Références

- `formal/Hypomnesis/Epistemics/Provenance.lean`
- Conventions et définition de fini : `.agentkanban/memory.md`
