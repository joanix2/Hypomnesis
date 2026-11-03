---
title: "HYP-061 · Automate d'états des commandes, délais, relances"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-060"
---

## Conversation

### user

**Ticket** HYP-061 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-060 · **Labels** python

#### Contexte

§9.7 : `Created` → `Validated` → `Authorized` → `Dispatched` → `Accepted` → `Completed`, plus les états d'échec ; idempotence.

#### Tâches proposées

- Automate explicite (table des transitions), états terminaux absorbants.
- Identifiants de commande, délais d'expiration, politique de relance.
- Déduplication par `command_id` : une commande non idempotente n'est jamais relancée automatiquement.

#### Critères d'acceptation

- Test exhaustif des transitions autorisées et interdites.
- Simulation de pannes de transport : aucune double exécution d'une commande non idempotente.

#### Fichiers concernés

- `src/hypomnesis/effects/commands.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
