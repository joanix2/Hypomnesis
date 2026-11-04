---
title: "HYP-020 · Lean F1a : variants et `match` général"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T18:38:53+01:00
description: "P0 · L · Vérification formelle (Lean) · dépend de HYP-003"
priority: P0
tags: [certification, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-020 · **Priorité** P0 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-003 · **Labels** lean

#### Contexte

Le fragment Lean (`formal/Hypomnesis/Core/`) ne couvre ni les variants ni le filtrage général, alors que la Core IR Python (`Construct`, `Match`, motifs `PCtor`, `PTuple`, `POr`, `PAlias`) les utilise partout, listes comprises. C'est le prérequis du pont de certificats.

#### Tâches proposées

- Syntaxe : déclarations de types variants (un environnement de déclarations Σ), `construct`, `match` avec motifs.
- Typage des motifs (contexte produit par un motif) et des `match`.
- Évaluation : filtrage premier bras gagnant ; `Match_failure` devient un résultat distinct de `stuck`.
- Étendre `eval_safe` : un terme bien typé ne rend jamais `stuck` (il peut rendre `matchFailure`).
- Étendre `typeOf` et ses preuves de correction et complétude ; mettre à jour la table de correspondance de `Syntax.lean`.

#### Critères d'acceptation

- `lake build` passe ; aucun `sorry` ; audit des axiomes inchangé.
- `docs/verification/proprietes.md` : P1–P6 annoncés pour le fragment étendu.
- Les listes du prélude s'expriment dans le fragment (`[]` et `::` comme variant).

#### Fichiers concernés

- `formal/Hypomnesis/Core/`
- `formal/Audit.lean`

#### Références

- `docs/verification/proprietes.md`
- `docs/verification/strategie.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan (suite du chemin critique, à la demande de l'utilisateur).

Choix de modélisation, faits pour éviter les inductifs imbriqués (`Expr` contenant `List Expr`) et mutuels, qui compliquent fortement les récurrences en Lean :

- **Signature Σ monomorphisée** : `Sig := List (List Ty)`. L'entrée `d` donne les types d'argument des constructeurs de l'instance de type de données `d`, par exemple `int list` : `[unit, prod int (data d)]`. Le décodeur (non fiable, HYP-026) instancie les types paramétrés ; le noyau prouvé ne fait aucune substitution. Le terme reste monomorphe jusqu'à HYP-023.
- **Constructeur** : `construct d c e`. Un constructeur nullaire porte `unit`.
- **Filtrage** : `case x p corps sinon` puis `fail t`, en chaîne binaire. Le décodeur traduit `Match(s, bras)` en `let s in case (var 0) p₁ b₁ (case (var 0) p₂ b₂ (fail t))`. Une garde se traduit en dupliquant la suite dans le corps ; c'est sûr, car le langage est pur.
- **Motifs** : `wild`, `var`, `int`, `bool`, `pair`, `ctor c p`. Ils lient leurs variables « la plus récente d'abord », dans l'ordre de l'environnement. Les alternatives et alias sont rejetés par le décodeur tant qu'ils ne sont pas formalisés.
- **Résultat** `matchFail`, distinct de `stuck` : la sûreté reste « jamais `stuck` ».

Théorèmes à étendre : `eval_safe`, `typeOf_sound` et `typeOf_complete` (avec `patTypeOf`), unicité, décidabilité, `eval_fuel_mono`.

### user

### agent

Implémenté et prouvé (aucun `sorry` ; axiomes : `propext` et `Quot.sound` uniquement).

- **Syntaxe** : `Ty.data d`, signature monomorphisée `Sig := List (List Ty)`, motifs `Pat` (joker, variable, littéraux, paire, constructeur), `Expr.construct`, `Expr.case` (chaîne binaire) et `Expr.fail`.
- **Typage** : `PatTy sig` et `HasType sig` paramétrés par la signature.
- **Évaluation** : `Val.con`, `Res.matchFail` (distinct de `stuck`), `matchPat`.
- **Preuves étendues** :
  - `eval_safe` (jamais `stuck`) ;
  - `matchPat_sound` (filtrage bien typé) ;
  - `patTypeOf_sound` et `patTypeOf_complete` ;
  - `typeOf_sound` et `typeOf_complete` (avec décidabilité et unicité) ;
  - `eval_fuel_mono`.
- **Exemple** (`Examples.lean`) : `length [1; 2; 3]` s'évalue à `3`. Son typage est démontré **par calcul** (`decide`) au moyen du vérificateur prouvé, d'où `program_never_stuck`.

Critères d'acceptation :
- `lake build` passe, aucun `sorry`, audit des axiomes inchangé : oui (`./scripts/validate.sh lean`) ;
- P1 à P6 annoncés pour le fragment étendu dans `proprietes.md` (P14 à P16 ajoutés) : oui ;
- les listes du prélude s'expriment dans le fragment : oui, comme instance monomorphisée (`int list` dans l'exemple).

Restent hors du fragment : records (HYP-021), motifs alternatifs et alias, exhaustivité (HYP-022), polymorphisme (HYP-023). Le décodeur de HYP-026 devra les rejeter.

La tâche peut passer en `done`.

### user
