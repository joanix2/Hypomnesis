---
title: "HYP-162 · Bibliothèque Units et exemple mécanique"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P2 · S · Déclarations d'unités/conversions et migration de l'exemple mécanique"
priority: P2
tags: [dsl, exemples, compilateur]
---

## Conversation

### user

**Ticket** HYP-162 · **Priorité** P2 · **Taille** S · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-161 · **Labels** dsl, exemples

#### Contexte

Sous-ticket de HYP-056, après la prise en charge des types dimensionnels par HYP-161.

#### Tâches proposées

- Déclarer les dimensions de base et conversions de la bibliothèque `Units`.
- Réécrire `examples/mechanics/units.hyp` pour utiliser les nouveaux types.
- Valider les types inférés dans l'exemple.

#### Critères d'acceptation

- Les dimensions de base et conversions requises sont déclarées dans la bibliothèque, sans logique d'unités ajoutée au noyau.
- L'exemple mécanique compile et ses types principaux sont vérifiés par des tests.

#### Fichiers concernés

- `examples/mechanics/units.hyp`
- bibliothèque de démonstration `Units`
- `tests/`

#### Références

- Parent : HYP-056, `.agentkanban/tasks/task_20261103_hyp056_types-dimensionnels.md`.
- Prérequis : HYP-161.

### user
