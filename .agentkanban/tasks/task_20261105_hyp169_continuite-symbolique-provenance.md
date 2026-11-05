---
title: "HYP-169 · Préserver l'état symbolique aux frontières de services"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · S · Types, identité des faits, provenance, hypothèses et validations conservés"
priority: P1
tags: [moteur-symbolique, epistemique, effets]
---

## Conversation

### user

**Ticket** HYP-169 · **Priorité** P1 · **Taille** S · **Epic** Exécution multi-services · **Dépend de** HYP-168 · **Labels** moteur-symbolique, epistemique

#### Contexte

Sous-ticket de HYP-153 portant sur l'état symbolique qui traverse les frontières des fournisseurs.

#### Tâches proposées

- Préserver types, identités de faits, provenance, statut d'hypothèse et résultats de validation lors des entrées/sorties de services.
- Refuser résultats invalides et éviter toute promotion d'une estimation/hypothèse en observation sans preuve.

#### Critères d'acceptation

- Une valeur de résultat réutilisée par le programme conserve ses types et identité/provenance attendues.
- Hypothèses et validations gardent leur statut ; les résultats invalides ne sont pas acceptés comme observations.
- Les tests couvrent les frontières de plusieurs services.

#### Fichiers concernés

- `src/hypomnesis/`
- `tests/`

#### Références

- Parent : HYP-153, `.agentkanban/tasks/task_20261104_hyp153_pipeline-multi-services.md`.
- Dépendance : HYP-168.

### user
