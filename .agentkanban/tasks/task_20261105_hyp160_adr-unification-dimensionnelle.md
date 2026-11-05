---
title: "HYP-160 · ADR des types dimensionnels"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P2 · S · Décision technique documentée pour la représentation et l'unification des dimensions"
priority: P2
tags: [architecture, dsl, metalangage]
---

## Conversation

### user

**Ticket** HYP-160 · **Priorité** P2 · **Taille** S · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-002 · **Labels** architecture, dsl

#### Contexte

Sous-ticket de HYP-056, requis pour rendre la conception vérifiable avant son implémentation. L'exigence existante impose un groupe abélien libre et une unification modulo AG ; ce ticket ne choisit pas de sémantique métier nouvelle.

#### Tâches proposées

- Comparer les représentations techniques possibles des dimensions et les conséquences de la normalisation/unification.
- Rédiger l'ADR attendue par HYP-056, en reliant le choix aux critères `m + s` refusé et `m / s * s` accepté.
- Identifier explicitement les limites et l'indépendance du noyau vis-à-vis des unités.

#### Critères d'acceptation

- Une ADR numérotée documente contexte, options considérées, choix technique, conséquences et limites.
- Le choix respecte les exigences dimensionnelles déjà fixées ; aucune unité ou politique métier supplémentaire n'est introduite.

#### Fichiers concernés

- `docs/adr/`
- `docs/architecture/m3-metalangage.md`

#### Références

- Parent : HYP-056, `.agentkanban/tasks/task_20261103_hyp056_types-dimensionnels.md`.
- Checklist parent : `.agentkanban/tasks/todo_20261105_hyp056_types-dimensionnels.md`.

### user
