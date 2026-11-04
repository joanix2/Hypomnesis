---
title: "HYP-131 · Extension VS Code : coloration syntaxique"
lane: qa
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T18:19:29+01:00
description: "P2 · S · Outillage et visualisation · dépend de HYP-002"
priority: P2
tags: [dsl, metalangage, outillage, vscode]
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

### agent

Demande utilisateur : ajouter la coloration et le linter VS Code. Plan intégré avec
HYP-132 : extension dans `editors/vscode`, grammaire TextMate testée avec le moteur
Oniguruma et contre les mots-clés Lark, configuration des commentaires et du repliement,
paquet VSIX générable localement. Pas de modification de la syntaxe du langage.
Checklist créée ; couloir conservé.

### user

### agent

Implémentation livrée dans `editors/vscode/` : association `.hyp`, grammaire TextMate,
commentaires imbriqués et documentaires, descriptions annotées, types, chaînes, nombres,
opérateurs, parenthèses et repliement. Six tests Oniguruma verts, dont correspondance exacte
des mots-clés avec Lark et tokenisation de `plaque.hyp` et `ventilation.hyp`.

`npm ci`, compilation TypeScript, tests, génération VSIX et audit npm réussis
(aucune vulnérabilité signalée). Paquet `editors/vscode/hypomnesis.vsix` généré, puis
installé dans VS Code : `hypomnesis.hypomnesis@0.1.0` confirmé par la liste des extensions.
Un test dans un hôte VS Code isolé confirme l'association du langage et les diagnostics.
Documentation d'installation ajoutée ; job CI de construction ajouté, non encore exécuté
à distance. Validation complète Python/Lean verte (671 tests), graphe rafraîchi.
Checklist complétée, couloir laissé à l'utilisateur, pas de push.

### user

### agent

Mise à jour du Kanban demandée : passage en `qa`. Implémentation enregistrée dans
`befd715`, puis adaptée aux déclarations natives dans `6e2962f`. Dernière validation
intégrée : 735 tests Python, Python/Lean verts, sept tests TextMate et test réel
d'hôte VS Code réussis. Validation humaine finale réservée à l'utilisateur.

### user
