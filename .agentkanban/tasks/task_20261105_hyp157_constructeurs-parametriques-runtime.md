---
title: "HYP-157 · Constructeurs et motifs paramétriques dans le pont runtime"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Intégration des données, motifs, records et couverture dans la sûreté polymorphe"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-157 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-156 · **Labels** lean, certification

#### Contexte

Sous-ticket de HYP-023 et suite du pont de sûreté établi par HYP-156. P47/P48 ne couvrent que des cas mono bornés ; ils ne valent pas preuve générale des données paramétriques.

#### Tâches proposées

- Intégrer les constructeurs et motifs nominaux au fragment runtime avec compatibilité explicite des signatures.
- Étendre la relation aux payloads de données paramétriques et à leurs instanciations.
- Préserver les preuves existantes pour les records, l'exhaustivité et `Coverage.Certified`.

#### Critères d'acceptation

- Constructeurs et motifs paramétriques sont reliés au véritable évaluateur dans le fragment documenté.
- Records et `Coverage.Certified` restent couverts, sans affaiblir les garanties antérieures de motifs ou de fuel.
- Des régressions positives et négatives couvrent arités/signatures incompatibles et l'exécution ; preuves sans `sorry`, audit mis à jour.

#### Fichiers concernés

- `formal/Hypomnesis/Core/PolySoundness.lean`
- `formal/Hypomnesis/Core/PolyTyping.lean`
- `formal/Hypomnesis/Core/Coverage.lean`
- `formal/Audit.lean`

#### Références

- Parent : HYP-023, `.agentkanban/tasks/task_20261103_hyp023_lean-polymorphisme.md`.
- Prérequis décomposé : HYP-156.
- `.agentkanban/tasks/todo_20261105_hyp023_polymorphisme-rang1.md`.

### agent

Ce ticket dépend de la relation polymorphe/sûreté de HYP-156 ; il ne reprend pas les exemples mono déjà prouvés comme s'ils satisfaisaient le critère général.

### user
