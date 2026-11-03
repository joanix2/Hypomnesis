---
title: "HYP-051 · Problem IR : variables, domaines, contraintes, objectifs"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 4 — Raisonnement hybride · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-051 · **Priorité** P0 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§13.3 : Problem IR (variables, domaines, contraintes, objectifs, états, actions, transitions).

#### Tâches proposées

- `ir/problem.py` : structures immuables ; construction depuis le langage.
- Sérialisation JSON avec schéma versionné.

#### Critères d'acceptation

- La contrainte du scénario MVP (épaisseur dans une plage, rigidité) s'exprime en Problem IR.

#### Fichiers concernés

- `src/hypomnesis/ir/problem.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
