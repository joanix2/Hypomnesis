---
title: "HYP-158 · Vérifier le véritable List.map du prélude"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Vérification du List.map réel et de ses dépendances dans le fragment polymorphe"
priority: P1
tags: [certification, lean, compilateur, metalangage]
---

## Conversation

### user

**Ticket** HYP-158 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-156, HYP-157 · **Labels** lean, certification

#### Contexte

Sous-ticket de HYP-023. Les exemples Lean `List.map`-équivalents ne satisfont pas le critère : il faut vérifier le véritable corps du prélude et ses dépendances `rev` et `fold_left`.

#### Tâches proposées

- Identifier et traduire dans le fragment le vrai `List.map` et les dépendances effectivement nécessaires.
- Vérifier le programme élaboré/certifié sans substituer un exemple isolé ni une monomorphisation présentée comme preuve polymorphe.
- Ajouter un cas exécuté utilisant plusieurs instanciations dans un même programme.

#### Critères d'acceptation

- Le véritable `List.map` du prélude et ses dépendances nécessaires sont acceptés par le checker/proof fragment retenu.
- Une régression vérifie plusieurs instanciations de types dans un même programme et son exécution.
- Les preuves/certificats utilisés sont audités et documentés ; aucun `sorry` ni dépendance manquante n'est masqué.

#### Fichiers concernés

- `src/hypomnesis/stdlib/prelude.hyp`
- `formal/Hypomnesis/Core/`
- `tests/`

#### Références

- Parent : HYP-023, `.agentkanban/tasks/task_20261103_hyp023_lean-polymorphisme.md`.
- Prérequis : HYP-156 et HYP-157.
- `TECHNICAL.md`, section Pipeline du langage.

### agent

Le critère vise le corps existant du prélude, pas une réécriture opportuniste ni un exemple `map` autonome. Si le fragment requis diffère de celui de HYP-156/157, documenter l'écart avant d'élargir la preuve.

### user
