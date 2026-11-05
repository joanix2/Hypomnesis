---
title: "HYP-163 · Formaliser les types dimensionnels et leur sûreté"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P2 · M · Modèle Lean des dimensions et sûreté du fragment typé"
priority: P2
tags: [lean, metalangage, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-163 · **Priorité** P2 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-156, HYP-161 · **Labels** lean, metalangage

#### Contexte

Sous-ticket formel de HYP-057. Il s'appuie sur le modèle de polymorphisme/runtimes de HYP-156 et les dimensions exécutables définies par HYP-161.

#### Tâches proposées

- Définir les types dimensionnels et leur interprétation dans le fragment Lean retenu.
- Relier le typage aux dimensions et établir le théorème de sûreté demandé pour ce fragment.
- Auditer et documenter les hypothèses, sans étendre les résultats au-delà du fragment prouvé.

#### Critères d'acceptation

- Le fragment dimensionnel et son interprétation sont formalisés.
- La sûreté du fragment est prouvée sans `sorry` et ses théorèmes figurent à l'audit.
- Des exemples/régressions lient le modèle Lean aux cas acceptés par HYP-161.

#### Fichiers concernés

- `formal/Hypomnesis/Dimensions/`
- `formal/Audit.lean`

#### Références

- Parent : HYP-057, `.agentkanban/tasks/task_20261103_hyp057_lean-dimensions.md`.
- Dépendances décomposées : HYP-156 et HYP-161.

### user
