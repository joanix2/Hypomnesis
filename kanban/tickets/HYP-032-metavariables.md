---
id: HYP-032
title: "Métavariables : inconnues explicites et contraintes"
status: backlog
priority: P1
size: M
epic: P2-EPISTEMIQUE
depends_on: [HYP-030]
labels: [python]
assignee: 
---

# HYP-032 — Métavariables : inconnues explicites et contraintes

## Contexte

§4.2 et §4.4 de `docs/architecture/m3-metalangage.md` : une valeur inconnue est une métavariable `?x : A`. Estimateurs, solveurs et générateurs la résolvent ; l'épaisseur de la plaque du scénario MVP en est le premier exemple.

## Tâches

- [ ] Représentation `MetaVar(id, type, constraints)` et état de résolution (non résolue, proposée avec grade, résolue).
- [ ] API : `propose(meta, value, grade, provenance)`, `resolve`, `conflict`.
- [ ] Interdire qu'une métavariable soit utilisée comme valeur concrète sans résolution (erreur explicite).

## Critères d'acceptation

- [ ] Tests : proposition par deux sources, sélection de la meilleure par le support, conflit détecté si incompatibles.

## Fichiers concernés

- `src/hypomnesis/epistemics/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
