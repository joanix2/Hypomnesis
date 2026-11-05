---
title: "HYP-166 · Bindings hôte et fournisseurs compatibles"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Résolution hôte de bindings compatibles sur les contrats de capacités"
priority: P1
tags: [metalangage, moteur-symbolique, contrats, effets]
---

## Conversation

### user

**Ticket** HYP-166 · **Priorité** P1 · **Taille** M · **Epic** Exécution multi-services · **Dépend de** HYP-165 · **Labels** moteur-symbolique, contrats

#### Contexte

Sous-ticket de HYP-152, après la formalisation du contrat de capacité par HYP-165. L'hôte configure les fournisseurs ; ce ticket n'impose ni protocole distant ni fournisseur précis.

#### Tâches proposées

- Réutiliser les décorateurs et le registre d'adaptateurs existants pour enregistrer/configurer les bindings.
- Séparer capacité et instance et résoudre les bindings depuis la configuration de l'hôte.
- Tester l'exécution du même programme avec deux implémentations compatibles.

#### Critères d'acceptation

- Un programme garde la même logique métier avec deux fournisseurs compatibles d'une capacité.
- Les erreurs de binding/contrat/disponibilité définies par HYP-165 sont propagées distinctement.
- Les tests couvrent les échanges effectifs et pas uniquement la découverte.

#### Fichiers concernés

- `src/hypomnesis/engine/adapters/`
- `src/hypomnesis/engine/`
- `tests/`

#### Références

- Parent : HYP-152, `.agentkanban/tasks/task_20261104_hyp152_bindings-services.md`.
- Prérequis : HYP-165.

### user
