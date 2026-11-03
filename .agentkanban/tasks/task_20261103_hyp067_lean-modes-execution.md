---
title: "HYP-067 · Lean F5c : dry-run sans dispatch, même terme dans les trois modes"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-064, HYP-065"
---

## Conversation

### user

**Ticket** HYP-067 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-064, HYP-065 · **Labels** lean

#### Contexte

§10.3 : la logique métier ne dépend pas du mode.

#### Tâches proposées

- Prouver : le handler dry-run ne produit aucun `dispatch`.
- Prouver : les trois handlers interprètent le même terme ; la simulation et la production ne diffèrent que par les réponses des opérations.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
