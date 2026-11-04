---
title: "HYP-131 · Extension VS Code : coloration syntaxique"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P2 · S · Outillage et visualisation · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-131 · **Priorité** P2 · **Taille** S · **Epic** Outillage et visualisation · **Dépend de** HYP-002 · **Labels** vscode, outillage

#### Contexte

Les fichiers `.hyp` n'ont aucune coloration dans VS Code. Une première extension déclare le langage et sa grammaire de coloration ; HYP-132 y ajoutera le linter.

#### Tâches proposées

- Extension dans `editors/vscode/` : association de `.hyp`, grammaire TextMate, commentaires, parenthèses, repliement.
- Colorer aussi les commentaires de description `(** … *)` (HYP-137).
- Test qui compare les mots-clés de la grammaire TextMate à ceux de `hypomnesis.lark`, pour éviter toute divergence.

#### Critères d'acceptation

- `plaque.hyp` et `ventilation.hyp` sont colorés correctement : mots-clés, types, chaînes, nombres, commentaires imbriqués.
- L'extension s'installe depuis un `.vsix` généré par une commande documentée.

#### Fichiers concernés

- `editors/vscode/`
- `src/hypomnesis/language/grammar/hypomnesis.lark`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`

