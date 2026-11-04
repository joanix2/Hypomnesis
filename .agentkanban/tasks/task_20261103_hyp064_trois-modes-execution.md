---
title: "HYP-064 · Modes simulation, dry-run et production comme handlers"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-060, HYP-063"
priority: P0
tags: [effets, moteur-symbolique, python, runtime]
---

## Conversation

### user

**Ticket** HYP-064 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-060, HYP-063 · **Labels** python

#### Contexte

§10.3 : un même programme utilise les trois modes sans modification de sa logique métier.

#### Tâches proposées

- Trois handlers de la même signature d'effets.
- Sélection du mode par la CLI ou l'application hôte, jamais par le programme.

#### Critères d'acceptation

- Le même fichier source s'exécute dans les trois modes.
- En dry-run, aucun actionneur n'est appelé (vérifié sur la trace).

#### Fichiers concernés

- `src/hypomnesis/effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
