---
title: "HYP-043 · Lean F5d : aller-retour JSON et conformité au schéma"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-042, HYP-021"
priority: P1
tags: [certification, contrats, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-043 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-042, HYP-021 · **Labels** lean

#### Contexte

Contrepartie prouvée de HYP-042, pour le fragment de types formalisé.

#### Tâches proposées

- Modéliser JSON et un sous-ensemble de JSON Schema (types, propriétés requises, `additionalProperties: false`).
- Prouver : `decode (encode v) = some v` et `ValTy v t → conforms (encode v) (schemaOf t)`.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Contracts/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
