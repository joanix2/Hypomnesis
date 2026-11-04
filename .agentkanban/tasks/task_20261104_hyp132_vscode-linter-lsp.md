---
title: "HYP-132 · Extension VS Code : linter du DSL par serveur de langage"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P2 · M · Outillage et visualisation · dépend de HYP-130, HYP-131"
---

## Conversation

### user

**Ticket** HYP-132 · **Priorité** P2 · **Taille** M · **Epic** Outillage et visualisation · **Dépend de** HYP-130, HYP-131 · **Labels** python, vscode, outillage

#### Contexte

Voir les erreurs du DSL directement dans l'éditeur, en réutilisant le vrai compilateur plutôt qu'une seconde analyse. Le protocole LSP évite de lier cet outillage à VS Code.

#### Tâches proposées

- Serveur de langage Python avec `pygls`, qui appelle le compilateur et publie ses diagnostics ; client `vscode-languageclient` dans l'extension.
- Trouver le langage M2 d'un programme M1 (`langage.json` le plus proche, ou réglage de l'extension).
- Vérifier à la frappe avec un délai d'attente, et annuler les analyses devenues obsolètes.
- Hors périmètre, à ouvrir en ticket si utile : survol des types, complétion, aller à la définition.

#### Critères d'acceptation

- Une erreur de syntaxe ou de type apparaît soulignée au bon endroit et dans l'onglet Problèmes, puis disparaît une fois corrigée.
- Les messages sont identiques à ceux de `hypomnesis check`.
- Tests du serveur sans VS Code, au niveau du protocole.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `editors/vscode/`
- `src/hypomnesis/lsp/`
- `pyproject.toml`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`
