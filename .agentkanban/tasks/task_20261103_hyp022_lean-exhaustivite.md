---
title: "HYP-022 · Lean F1c : un `match` exhaustif ne lève jamais `Match_failure`"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-020, HYP-010"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-022 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020, HYP-010 · **Labels** lean

#### Contexte

Une fois l'exhaustivité implémentée côté Python (HYP-010), on prouve sa contrepartie Lean.

#### Tâches proposées

- Définir `exhaustive : Σ → Ty → List Pattern → Bool` (même algorithme que HYP-010).
- Prouver : pour une valeur bien typée, des motifs exhaustifs dont au moins un bras sans garde la couvre, le filtrage réussit.
- Corollaire : un programme dont tous les `match` sont exhaustifs ne rend jamais `matchFailure`.

#### Critères d'acceptation

- Théorème prouvé et ajouté à l'audit.
- Tests croisés : Python et Lean donnent le même verdict sur un corpus.

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
