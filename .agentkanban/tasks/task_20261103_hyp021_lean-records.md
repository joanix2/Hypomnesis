---
title: "HYP-021 · Lean F1b : records et mise à jour fonctionnelle"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-020"
---

## Conversation

### user

**Ticket** HYP-021 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020 · **Labels** lean

#### Contexte

La Core IR a `Record`, `RecordUpdate`, `Field` et le motif `PRecord` ; ils ne sont pas formalisés.

#### Tâches proposées

- Ajouter les types records nominaux à Σ, ainsi que construction, accès, mise à jour et motif.
- Étendre sûreté, correction et complétude de `typeOf`.

#### Critères d'acceptation

- Preuves étendues sans `sorry`.
- Un exemple `#eval` reproduit `examples/basics/tour.hyp` (`deposit`).

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
