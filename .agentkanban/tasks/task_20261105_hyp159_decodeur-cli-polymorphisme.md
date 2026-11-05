---
title: "HYP-159 · Brancher les certificats polymorphes au décodeur et au CLI"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Intégration du vérificateur de certificats polymorphes et régressions CLI"
priority: P1
tags: [certification, compilateur, lean, cli]
---

## Conversation

### user

**Ticket** HYP-159 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-156, HYP-157, HYP-158 · **Labels** lean, certification, cli

#### Contexte

Sous-ticket d'intégration de HYP-023. Les types et preuves Lean ne suffisent pas à certifier le résultat réellement produit par l'élaboration et utilisé par le CLI.

#### Tâches proposées

- Étendre le format/décodeur de certificat au fragment polymorphe prouvé.
- Brancher le vérificateur au vrai chemin CLI sans relâcher les refus existants.
- Vérifier compatibilité des versions de certificats 1.0/1.1 mentionnées dans le plan parent.

#### Critères d'acceptation

- Le CLI vérifie un certificat polymorphe produit depuis le programme élaboré, dont le véritable `List.map`.
- Certificats altérés, hors-fragment ou incompatibles sont refusés explicitement ; les régressions historiques restent vertes.
- Tests, audit et documentation couvrent le format et le branchement ; aucune voie de repli permissive.

#### Fichiers concernés

- `src/hypomnesis/`
- `formal/`
- `tests/`
- `docs/`

#### Références

- Parent : HYP-023, `.agentkanban/tasks/task_20261103_hyp023_lean-polymorphisme.md`.
- Prérequis : HYP-156, HYP-157 et HYP-158.
- `.agentkanban/tasks/todo_20261105_hyp023_polymorphisme-rang1.md`.

### agent

Le ticket ne change pas le format ni la politique de compatibilité par anticipation : établir leur comportement à partir des contrats existants et signaler toute décision de version nécessitant l'utilisateur.

### user
