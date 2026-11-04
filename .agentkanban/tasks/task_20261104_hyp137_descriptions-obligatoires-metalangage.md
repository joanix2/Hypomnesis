---
title: "HYP-137 · Descriptions obligatoires dans le métalangage"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · M · Langage · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-137 · **Priorité** P1 · **Taille** M · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python, langage, llm

#### Contexte

Pour générer un prompt à partir d'un langage (HYP-138), chaque mot de ce langage doit porter sa description. Le lexeur rejette aujourd'hui tous les commentaires (`%ignore COMMENT`), et le prompt inclut le source brut.

#### Tâches proposées

- ADR : syntaxe et règles. Proposition : commentaires de description `(** … *)`, comme OCaml, rattachés selon leur position.
- Les conserver jusqu'à l'AST et les exposer aux outils ; pour les rattacher, préférer la position à des jetons dans toute la grammaire LALR.
- Erreur de compilation si un élément public d'un langage M2 n'a pas de description : module, type, champ, constructeur, valeur, procédure.
- Les programmes M1 ne sont pas concernés.
- Compléter les descriptions de `mecanique` et `ventilation`, y compris les unités et le sens de `None`.

#### Critères d'acceptation

- Retirer la description d'un champ donne une erreur qui nomme ce champ, à sa position.
- Les descriptions n'ont aucun effet sémantique : Core IR et certificats sont identiques avec ou sans elles (test de propriétés).
- Le test d'architecture passe toujours.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/language/grammar/hypomnesis.lark`
- `src/hypomnesis/language/parser.py`
- `src/hypomnesis/language/ast.py`
- `languages/mecanique/plaque.hyp`
- `languages/ventilation/ventilation.hyp`

#### Références

- Lié à HYP-012 : les signatures de modules définiront ce qui est public
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

**Avancement (2026-11-04).** Fait : l'extraction des descriptions `(** … *)` et des balises `@tag` par **position** (`language/docs.py`, sans toucher à la grammaire), conservée côté outils ; les descriptions de `mecanique` et `ventilation` (unités, sens de `None`, quand utiliser chaque procédure, squelette de programme) ; tests (`test_docs.py`) ; ADR 0009 (proposée).

Reste : l'**erreur de compilation** quand un élément public n'a pas de description (il faut d'abord la notion de « public », HYP-012) et le test de propriétés « Core IR et certificats identiques avec ou sans descriptions » (vrai par construction, puisque ce sont des commentaires pour la grammaire, mais à prouver par un test).

### agent

**Décisions de l'utilisateur (2026-11-04).**
- **« Public »** : tout élément déclaré dans un fichier source d'un langage M2 dont le nom ne commence pas par `_`, sans attendre HYP-012 (qui pourra restreindre la notion ensuite).
- **Balise `@interne`** : un élément portant `@interne` est **documenté mais non publié** dans le catalogue du prompt. Il reste soumis à l'obligation de description (une description est exigée, y compris pour un élément `@interne`), mais `llm/describe.py` ne l'inclut pas dans le catalogue ni dans `decrire`. Un élément en `_nom` n'a pas d'obligation de description et n'est jamais publié. À consigner dans l'ADR 0009 et dans `docs/language/reference.md`. Conséquence pour HYP-138 : le catalogue filtre sur cette balise.

### user
