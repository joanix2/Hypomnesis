---
title: "HYP-066 · Lean F5b : au plus une exécution des commandes non idempotentes"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Vérification formelle (Lean) · dépend de HYP-061"
priority: P0
tags: [effets, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-066 · **Priorité** P0 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-061 · **Labels** lean

#### Contexte

§9.7 et risque « Doubles commandes » (§19).

#### Tâches proposées

- Modéliser automate, journal, relances, pertes et duplications de messages.
- Prouver : une commande non idempotente est exécutée au plus une fois, quelles que soient les pannes modélisées.
- Prouver : les états terminaux sont absorbants.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
