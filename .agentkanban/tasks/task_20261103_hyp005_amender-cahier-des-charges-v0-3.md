---
title: "HYP-005 · Amender le cahier des charges en v0.3"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · S · Fondations et gouvernance · dépend de HYP-003"
priority: P1
tags: [architecture, documentation, humain, mvp]
---

## Conversation

### user

**Ticket** HYP-005 · **Priorité** P1 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-003 · **Labels** humain, doc

> **Décision humaine requise** : ce ticket ne doit pas être réalisé par un agent seul.

#### Contexte

Deux propositions attendent une décision : l'objectif OBJ-11 « Vérification formelle » et ses critères d'acceptation (§4 de `docs/verification/proprietes.md`), et la décomposition des statuts épistémiques du §7.1 en trois axes (existence, support, cohérence ; §4.3 de `docs/architecture/m3-metalangage.md`).

#### Tâches proposées

- Décider de l'adoption de chaque proposition.
- Créer `docs/specification/cahier-des-charges-v0.3.md` à partir de `docs/specification/cahier-des-charges-v0.2.md`, avec un journal des changements en tête.
- Passer l'ADR 0006 à « acceptée » ou « rejetée ».

#### Critères d'acceptation

- La v0.3 existe ; la v0.2 est conservée telle quelle.
- Les tickets du lot P2-EPISTEMIQUE sont cohérents avec la décision sur les statuts.

#### Fichiers concernés

- `docs/specification/`
- `docs/adr/0006-m3-theorie-des-types-a-deux-niveaux.md`

#### Références

- `docs/verification/proprietes.md`
- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
