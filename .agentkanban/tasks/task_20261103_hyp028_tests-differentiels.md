---
title: "HYP-028 · Tests différentiels interpréteur Python ↔ sémantique Lean"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-026"
priority: P1
tags: [certification, compilateur, lean, metalangage, python, runtime, tests]
---

## Conversation

### user

**Ticket** HYP-028 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-026 · **Labels** python, lean, tests

#### Contexte

La fidélité de l'interpréteur Python à la sémantique prouvée n'est couverte que par des tests (`docs/verification/strategie.md`).

#### Tâches proposées

- Générateur Hypothesis de termes bien typés du fragment (génération dirigée par les types).
- Exécuter chaque terme en Python et avec `hypomnesis-check eval` ; comparer valeurs, `timeout` et `matchFailure`.
- Rendre le budget comparable des deux côtés (même notion de pas, ou comparaison des seuls résultats terminés).

#### Critères d'acceptation

- Au moins 500 termes par exécution de CI, aucune divergence.
- Une divergence introduite volontairement dans l'interpréteur Python est détectée.

#### Fichiers concernés

- `tests/differential/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
