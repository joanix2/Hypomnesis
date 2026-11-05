---
title: "HYP-168 · Exécution des pipelines et branchements paresseux"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Exécuter les étapes par capacité et uniquement sur le chemin choisi"
priority: P1
tags: [moteur-symbolique, metalangage, effets]
---

## Conversation

### user

**Ticket** HYP-168 · **Priorité** P1 · **Taille** M · **Epic** Exécution multi-services · **Dépend de** HYP-166, HYP-167 · **Labels** moteur-symbolique, effets

#### Contexte

Sous-ticket de HYP-153, après les contrats/bindings et contrôles statiques de HYP-165 à HYP-167. L'interpréteur ne migre pas arbitrairement chez un tiers.

#### Tâches proposées

- Articuler la procédure existante avec des étapes liées à des capacités.
- Enchaîner les résultats et exécuter dépendances de données et branchements selon le chemin réellement pris.
- Refuser les bindings ambigus et ne pas substituer silencieusement un solveur.

#### Critères d'acceptation

- Une procédure réelle traverse plusieurs fournisseurs et réutilise leurs résultats dans un calcul symbolique et un branchement.
- Un branchement non exécuté ne déclenche aucun appel de son service.
- Les tests montrent des choix de binding explicites, sans substitution silencieuse.

#### Fichiers concernés

- `src/hypomnesis/`
- `tests/`

#### Références

- Parent : HYP-153, `.agentkanban/tasks/task_20261104_hyp153_pipeline-multi-services.md`.
- Prérequis décomposés : HYP-166 et HYP-167 ; parent amont HYP-152.

### user
