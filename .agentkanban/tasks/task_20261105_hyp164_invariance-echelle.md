---
title: "HYP-164 · Prouver l'invariance dimensionnelle par changement d'échelle"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P2 · S · Théorème de paramétricité des fonctions polymorphes en dimension"
priority: P2
tags: [lean, metalangage, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-164 · **Priorité** P2 · **Taille** S · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-163 · **Labels** lean, metalangage

#### Contexte

Sous-ticket de HYP-057 et suite de la formalisation/sûreté HYP-163.

#### Tâches proposées

- Formaliser le changement d'échelle sur l'interprétation dimensionnelle retenue.
- Prouver la commutation des fonctions polymorphes en dimension avec cette transformation.

#### Critères d'acceptation

- Le théorème d'invariance par changement d'échelle est démontré pour le fragment annoncé, sans `sorry`.
- Les hypothèses, portée et résultat sont inscrits à l'audit et documentés.

#### Fichiers concernés

- `formal/Hypomnesis/Dimensions/`
- `formal/Audit.lean`

#### Références

- Parent : HYP-057, `.agentkanban/tasks/task_20261103_hyp057_lean-dimensions.md`.
- Prérequis : HYP-163.

### user
