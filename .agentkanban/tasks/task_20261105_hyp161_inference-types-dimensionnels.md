---
title: "HYP-161 · Types et unification dimensionnels"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P2 · M · Inférence des dimensions par unification modulo groupe abélien libre"
priority: P2
tags: [compilateur, dsl, metalangage, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-161 · **Priorité** P2 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-160 · **Labels** compilateur, dsl

#### Contexte

Sous-ticket d'implémentation de HYP-056. Le métalangage exprime les dimensions ; le noyau ne connaît pas les unités.

#### Tâches proposées

- Représenter les dimensions comme produits formels de générateurs avec exposants entiers.
- Intégrer leur unification modulo groupe abélien libre au typeur et fournir des diagnostics utiles.
- Ajouter des régressions positives et négatives aux expressions et signatures annotées pertinentes.

#### Critères d'acceptation

- `m + s` est refusé avec diagnostic de dimension incompatible.
- `m / s * s` est accepté et inféré comme `m`.
- Les types principaux sont inférés et les contraintes dimensionnelles sont résolues sans spécialiser le noyau aux unités.

#### Fichiers concernés

- `src/hypomnesis/language/typesystem/`
- `tests/`
- `docs/adr/`

#### Références

- Parent : HYP-056, `.agentkanban/tasks/task_20261103_hyp056_types-dimensionnels.md`.
- ADR préalable : HYP-160.
- Spécification de contexte : `docs/architecture/m3-metalangage.md` §5.3 et §6.5.

### user
