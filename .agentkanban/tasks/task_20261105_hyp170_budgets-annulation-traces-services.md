---
title: "HYP-170 · Erreurs, budgets et traces des pipelines"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Délais, annulation, relances non dupliquantes et observabilité"
priority: P1
tags: [moteur-symbolique, effets, observabilite]
---

## Conversation

### user

**Ticket** HYP-170 · **Priorité** P1 · **Taille** M · **Epic** Exécution multi-services · **Dépend de** HYP-168, HYP-169 · **Labels** moteur-symbolique, effets, observabilite

#### Contexte

Sous-ticket de HYP-153 pour les limites d'exécution et le diagnostic des pipelines multi-services.

#### Tâches proposées

- Fixer des budgets/délais bornés et propager erreur et annulation.
- Garantir qu'une relance ne duplique pas une action non idempotente.
- Tracer étape, service, demande, résultat et cause d'échec.

#### Critères d'acceptation

- Panne, timeout, résultat invalide et annulation ont des comportements et tests explicites.
- Une relance ne duplique pas une action non idempotente.
- Les traces identifient les étapes/services et les causes de succès/échec sans données sensibles injustifiées.

#### Fichiers concernés

- `src/hypomnesis/`
- `tests/`
- `docs/`

#### Références

- Parent : HYP-153, `.agentkanban/tasks/task_20261104_hyp153_pipeline-multi-services.md`.
- Prérequis : HYP-168 et HYP-169.

### user
