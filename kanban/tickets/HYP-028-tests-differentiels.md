---
id: HYP-028
title: "Tests différentiels interpréteur Python ↔ sémantique Lean"
status: backlog
priority: P1
size: M
epic: FORMEL
depends_on: [HYP-026]
labels: [python, lean, tests]
assignee: 
---

# HYP-028 — Tests différentiels interpréteur Python ↔ sémantique Lean

## Contexte

La fidélité de l'interpréteur Python à la sémantique prouvée n'est couverte que par des tests (`docs/verification/strategie.md`).

## Tâches

- [ ] Générateur Hypothesis de termes bien typés du fragment (génération dirigée par les types).
- [ ] Exécuter chaque terme en Python et avec `hypomnesis-check eval` ; comparer valeurs, `timeout` et `matchFailure`.
- [ ] Rendre le budget comparable des deux côtés (même notion de pas, ou comparaison des seuls résultats terminés).

## Critères d'acceptation

- [ ] Au moins 500 termes par exécution de CI, aucune divergence.
- [ ] Une divergence introduite volontairement dans l'interpréteur Python est détectée.

## Fichiers concernés

- `tests/differential/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
