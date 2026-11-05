---
title: "HYP-167 · Vérification statique et permissions des bindings"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · S · Séparer imports et bindings et valider avant tout appel de service"
priority: P1
tags: [metalangage, contrats, securite, lsp]
---

## Conversation

### user

**Ticket** HYP-167 · **Priorité** P1 · **Taille** S · **Epic** Exécution multi-services · **Dépend de** HYP-165, HYP-166 · **Labels** metalangage, contrats, lsp

#### Contexte

Sous-ticket de HYP-152. Les imports de bibliothèques symboliques ne doivent jamais accorder de permissions ni lancer un service.

#### Tâches proposées

- Séparer l'import symbolique du binding d'exécution dans le modèle existant.
- Garantir que check/LSP n'importe aucun adaptateur et ne démarre aucun service.
- Vérifier contrats et permissions avant chaque appel d'exécution.

#### Critères d'acceptation

- Les imports n'accordent aucun droit et n'activent aucun service.
- Check/LSP restent statiques, sans import d'adaptateur ni démarrage de service.
- Les permissions et contrats sont validés avant chaque appel ; des tests couvrent les refus.

#### Fichiers concernés

- `src/hypomnesis/engine/`
- `src/hypomnesis/lsp/`
- `tests/`

#### Références

- Parent : HYP-152, `.agentkanban/tasks/task_20261104_hyp152_bindings-services.md`.
- Prérequis : HYP-165 et HYP-166.

### user
