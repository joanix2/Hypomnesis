---
title: "HYP-063 · Transport JSON par fichiers et périphériques simulés"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-062"
priority: P0
tags: [contrats, effets, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-063 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-062 · **Labels** python

#### Contexte

§9.5 : fichiers JSON pour le MVP, contrat séparé du transport ; capteurs et actionneurs simulés.

#### Tâches proposées

- Interface de transport ; implémentations mémoire et fichiers.
- Capteur de température simulé, actionneur de ventilateur simulé, avec manifestes et schémas.
- Enregistrement et rejeu de scénarios.

#### Critères d'acceptation

- Tous les messages passent par l'enveloppe `envelope/1.0.0`.
- Un scénario enregistré se rejoue à l'identique.

#### Fichiers concernés

- `src/hypomnesis/effects/transports/`
- `examples/robotics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
