---
title: "HYP-004 · Pousser la branche et valider la CI (Python et preuves)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · S · Fondations et gouvernance · dépend de HYP-003"
---

## Conversation

### user

**Ticket** HYP-004 · **Priorité** P0 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-003 · **Labels** humain, ci

> **Décision humaine requise** : ce ticket ne doit pas être réalisé par un agent seul.

#### Contexte

La branche `phase-0-1-langage-minimal` n'a jamais été poussée : le workflow `.github/workflows/ci.yml` (jobs `test` et `proofs`) n'a donc jamais tourné sur GitHub. Le job `proofs` installe elan et lance `lake build`.

#### Tâches proposées

- Pousser la branche vers `origin` (décision humaine).
- Observer les deux jobs ; corriger ce qui échoue (versions Python 3.11/3.13, installation d'elan, cache).

#### Critères d'acceptation

- Les jobs `test` et `proofs` sont verts sur la branche.
- Le job `proofs` échoue si l'on introduit volontairement un `sorry` (vérifié une fois puis annulé).

#### Fichiers concernés

- `.github/workflows/ci.yml`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
