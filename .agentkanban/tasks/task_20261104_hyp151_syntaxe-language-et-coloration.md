---
title: "HYP-151 · Cohérence des déclarations language et coloration VS Code"
lane: todo
created: 2026-11-04T23:08:20+01:00
updated: 2026-11-04T23:08:20+01:00
description: "P2 · M · Métalangage et outillage · syntaxe des métadonnées et coloration sur le poste courant"
priority: P2
tags: [metalangage, dsl, outillage, vscode]
---

## Conversation

### user

**Ticket** HYP-151 · **Priorité** P2 · **Taille** M · **Epic** Métalangage et outillage · **Dépend de** HYP-131, HYP-147 · **Labels** vscode, metalangage

la syntaxe est différente et il n'y a pas de coloration syntaxique :

```hyp
language arithmetique = {
  version = "1.0.0";
  description = "Arithmétique entière réutilisable, sans entrée/sortie."
}
```

#### Contexte

Signalement sur [arithmetique/langage.hyp](../../demo/languages/arithmetique/langage.hyp).
L'utilisateur constate une différence de syntaxe et une absence de coloration.
La déclaration language est une forme native introduite par HYP-147 ; ne
pas décider d'une nouvelle syntaxe à la place de l'utilisateur.

#### Tâches proposées

- Comparer la déclaration language aux autres déclarations du métalangage :
  métadonnées, descriptions et imports. Expliciter les différences et proposer
  une harmonisation à faire arbitrer avant tout changement incompatible.
- Reproduire le défaut sur le poste courant : association .hyp, extension
  active, version installée et grammaire embarquée.
- Vérifier la tokenisation réelle du bloc : language, nom déclaré, champs,
  chaînes, opérateurs et ponctuation ; corriger les surfaces manquantes.
- Ajouter un test TextMate du bloc exact et documenter installation/
  rechargement si la grammaire source est correcte mais l'extension inactive
  ou obsolète.

#### Critères d'acceptation

- La différence de syntaxe est expliquée et l'éventuel choix d'harmonisation
  est validé par l'utilisateur, sans migration silencieuse.
- Le fichier est reconnu comme Hypomnesis et sa coloration est vérifiée
  dans un hôte VS Code, pas seulement par lecture du JSON de grammaire.
- Un test couvre la déclaration exacte ci-dessus ; les autres formes
  continuent à être colorées.

#### Fichiers concernés

- `demo/languages/arithmetique/langage.hyp`
- `editors/vscode/`
- `src/hypomnesis/language/grammar/hypomnesis.lark`
- Documentation des déclarations de langage et de l'installation VS Code.

### agent

Signalement enregistré, sans modification de syntaxe ni implémentation.
Constat initial : language est déjà présent dans les mots-clés de la
grammaire TextMate du dépôt. Cela ne prouve pas que cette version de
l'extension est installée/active sur le poste courant ; cette frontière
devra être vérifiée. Le nom déclaré et les métadonnées peuvent aussi
nécessiter des règles dédiées.

### user
