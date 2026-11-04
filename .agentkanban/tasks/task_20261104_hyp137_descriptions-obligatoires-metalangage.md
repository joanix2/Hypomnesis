---
title: "HYP-137 · Descriptions obligatoires dans le métalangage"
lane: qa
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T14:55:00+01:00
description: "P1 · M · Langage · dépend de HYP-002"
priority: P1
tags: [documentation, dsl, llm, metalangage, python]
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

### agent

**Compte rendu (2026-11-04, WIP — `validate.sh rapide`/`complet` non relancés, voir « Reste »).**

Fait :
- Instantanés du catalogue rendu (`tests/unit/snapshots/catalogue_{mecanique,ventilation}.md`, test dans `test_describe.py`), écrits **avant** de toucher aux langages : octet pour octet identiques après les changements (test vert). Commit `2c3908c`.
- `language/docs.py` : extraction par **lexage** (`parser.lex` = `Lark.lex(dont_ignore=True)`) au lieu de la regex `_DOC` ; `Declaration.span`, `Declaration.internal`, descriptions de constructeurs (`(** … *)` avant `| Ctor`), `is_public`, `published`, `missing_descriptions`.
- `engine/language.py` : `MissingDescriptionError(HypomnesisError, LanguageError)` (nomme l'élément, le fichier, la position ; `render` souligne le nom), `load_language(root, *, strict=True)`. `errors.py` et `cli.py` non touchés (la double héritance fait que `decrire` l'attrape comme `LanguageError`).
- `llm/describe.py` : `@interne` exclu du catalogue (et ses membres) ; `@discret` : membre listé sans description.
- `plaque.hyp`, `ventilation.hyp` : tout élément non publié porte `@interne` (+ description), les champs de `Plaque.estimateur` portent `@discret` (pour que le prompt reste identique), type `estimateur` reformaté sur plusieurs lignes.
- Tests : `tests/unit/test_language_docs.py` (règle, position, `_`, `@interne`, `@discret`, lexage, propriétés Core IR + certificat identiques avec/sans descriptions sur langages et exemples). `test_llm.py` : le test « langage non documenté » utilise `strict=False` (+ vérifie l'erreur en strict).
- Docs : ADR 0009 (décisions 6 et 7), `docs/language/reference.md`, `TECHNICAL.md` (section HYP-137).
- Lancés et verts : `test_language_docs`, `test_docs`, `test_describe`, `test_prompting`, `test_llm`, `tests/integration/test_languages`, `test_examples` ; `ruff check`/`format` sur mes fichiers.

Écarts / décisions :
- Item 6 : `lexer_callbacks` écarté au profit de `Lark.lex(dont_ignore=True)` (pas d'état partagé avec l'analyseur mis en cache). Les commentaires restent non imbriqués (comme le lexeur) : `(* … (** … *) … *)` est une erreur de syntaxe, pas un cas à gérer.
- Ajout de `@discret` (non demandé) : les trois champs publics de `Plaque.estimateur` devaient être décrits mais listés sans description dans le prompt mesuré.
- Les membres d'un élément `@interne` (champs, éléments d'un module) sont **exemptés** de description (l'élément `@interne` lui-même doit être décrit) ; un nom `_` exempte aussi ses membres. À valider par l'utilisateur.
- Un champ/constructeur écrit sur la même ligne que son type ne peut pas être décrit (limite du rattachement positionnel).
- `tests/unit/test_llm.py` est aussi touché par HYP-139 : seul mon hunk (import `pytest`/`MissingDescriptionError`, `strict=False`) est à moi.

Reste :
- Lancer `./scripts/validate.sh rapide` puis `complet` (test d'architecture non lancé explicitement), corriger si besoin.
- Passer la fiche en `qa` une fois `complet` vert ; cocher la dernière case de la checklist.
- `cli.py` (HYP-130) : si une commande charge un langage, vérifier qu'elle affiche `str(exc)`/`exc.render()` de `MissingDescriptionError`.

### user
