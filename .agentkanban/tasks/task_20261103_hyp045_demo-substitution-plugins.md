---
title: "HYP-045 · Démonstration : deux plugins derrière la même interface"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · S · Phase 3 — Extensions et contrats · dépend de HYP-044"
priority: P1
tags: [capacites, contrats, exemple, moteur-symbolique, python, tests]
---

## Conversation

### user

**Ticket** HYP-045 · **Priorité** P1 · **Taille** S · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-044 · **Labels** python, exemple

#### Contexte

Critère d'acceptation du §16.4 et hypothèse H6.

#### Tâches proposées

- Deux estimateurs d'épaisseur (règle simple, régression) derrière la même interface.
- Le même programme fonctionne avec l'un ou l'autre, sur simple changement de configuration.

#### Critères d'acceptation

- Test d'intégration qui exécute le programme avec chaque plugin sans modifier le source.

#### Fichiers concernés

- `examples/mechanics/`
- `tests/integration/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
