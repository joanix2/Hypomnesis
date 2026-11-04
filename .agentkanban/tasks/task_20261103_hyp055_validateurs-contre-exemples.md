---
title: "HYP-055 · Validateurs et contre-exemples"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 4 — Raisonnement hybride · dépend de HYP-052"
priority: P1
tags: [capacites, moteur-symbolique, python, solveurs, tests, validateurs]
---

## Conversation

### user

**Ticket** HYP-055 · **Priorité** P1 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-052 · **Labels** python

#### Contexte

§11.6 : vérification des résultats et production éventuelle de contre-exemples.

#### Tâches proposées

- Interface `Validator` concrète : rend une preuve d'acceptation ou un contre-exemple vérifiable.
- Validateur géométrique pour la plaque.

#### Critères d'acceptation

- Un rejet est toujours accompagné d'un contre-exemple que l'on peut revérifier indépendamment.

#### Fichiers concernés

- `src/hypomnesis/engine/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
