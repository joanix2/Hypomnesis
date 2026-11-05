---
title: "HYP-165 · Contrats typés des capacités de service"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · S · Modèle de contrat pour identité/version, échanges et erreurs de capacité"
priority: P1
tags: [metalangage, moteur-symbolique, contrats]
---

## Conversation

### user

**Ticket** HYP-165 · **Priorité** P1 · **Taille** S · **Epic** Exécution multi-services · **Dépend de** HYP-060, HYP-062, HYP-063, HYP-147 · **Labels** metalangage, contrats

#### Contexte

Sous-ticket de HYP-152, sans décision de syntaxe ni de transport : ces choix restent ouverts dans le parent.

#### Tâches proposées

- Définir les informations typées d'une capacité indépendante de son instance : identité/version, entrées/sorties, erreurs et disponibilité.
- Distinguer erreurs d'absence de binding, incompatibilité de contrat et indisponibilité.
- Ajouter des tests de contrat sur les échanges, pas seulement la découverte.

#### Critères d'acceptation

- Le contrat distingue clairement capacité et instance et décrit les entrées/sorties/version.
- Les trois erreurs nommées sont distinctes et ne produisent aucune réponse de succès fictive.
- Des tests vérifient les échanges conformes et invalides.

#### Fichiers concernés

- `src/hypomnesis/engine/`
- `tests/`
- `docs/`

#### Références

- Parent : HYP-152, `.agentkanban/tasks/task_20261104_hyp152_bindings-services.md`.
- Checklist parent : `.agentkanban/tasks/todo_20261105_hyp152_bindings-services.md`.

### user
