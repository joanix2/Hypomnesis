---
title: "HYP-032 · Métavariables : inconnues explicites et contraintes"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-030"
---

## Conversation

### user

**Ticket** HYP-032 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-030 · **Labels** python

#### Contexte

§4.2 et §4.4 de `docs/architecture/m3-metalangage.md` : une valeur inconnue est une métavariable `?x : A`. Estimateurs, solveurs et générateurs la résolvent ; l'épaisseur de la plaque du scénario MVP en est le premier exemple.

#### Tâches proposées

- Représentation `MetaVar(id, type, constraints)` et état de résolution (non résolue, proposée avec grade, résolue).
- API : `propose(meta, value, grade, provenance)`, `resolve`, `conflict`.
- Interdire qu'une métavariable soit utilisée comme valeur concrète sans résolution (erreur explicite).

#### Critères d'acceptation

- Tests : proposition par deux sources, sélection de la meilleure par le support, conflit détecté si incompatibles.

#### Fichiers concernés

- `src/hypomnesis/epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
