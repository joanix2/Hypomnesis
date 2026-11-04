---
title: "HYP-026 · Pont F3c : exécutable Lean `hypomnesis-check`"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T18:47:41+01:00
description: "P0 · M · Vérification formelle (Lean) · dépend de HYP-025, HYP-020"
priority: P0
tags: [certification, lean]
---

## Conversation

### user

**Ticket** HYP-026 · **Priorité** P0 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-025, HYP-020 · **Labels** lean

#### Contexte

Le vérificateur `typeOf`, prouvé correct, doit pouvoir lire un certificat JSON produit par Python.

#### Tâches proposées

- Ajouter une cible `lean_exe hypomnesis-check` dans `formal/lakefile.toml`.
- Décoder le JSON (`Lean.Json`) vers `Expr`, `Ty` et Σ ; retourner un code de sortie et un diagnostic en cas de refus.
- Sous-commande `eval` exposant l'interpréteur de référence (utilisée par HYP-028).

#### Critères d'acceptation

- `lake exe hypomnesis-check cert.json` accepte les certificats des exemples et refuse un certificat altéré à la main.
- Le décodeur est séparé du noyau prouvé : seul `typeOf` fait partie de la base de confiance.

#### Fichiers concernés

- `formal/lakefile.toml`
- `formal/Main.lean`
- `formal/Hypomnesis/Certificate.lean`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan.

**Le décodeur est hors de la base de confiance.** Il traduit le certificat dans le fragment Lean ; seul `typeOf` (prouvé) décide du typage. Un décodeur fautif peut faire rejeter un bon programme, mais pas accepter un programme mal typé : il ne produit que des termes que `typeOf` vérifie.

Traduction :
- le programme devient une chaîne de `letE` (une par définition atteignable), terminée par le n-uplet des définitions racines (celles du programme, après le prélude) ;
- **monomorphisation** : une définition polymorphe est spécialisée à chaque instanciation utilisée ; seules les définitions atteignables depuis les racines sont traduites. Deux passes : collecte des instances jusqu'au point fixe, puis émission dans l'ordre des définitions ;
- types de données instanciés à la demande dans la signature `Sig` (récursion comprise) ; n-uplets en paires imbriquées ; lambdas et applications à plusieurs arguments curryfiées ;
- `match` : `letE s (case (var 0) …)` avec décalage des indices, gardes par duplication de la suite ; `let rec` d'une seule fonction : `fix` ;
- primitives : `int.add`, `int.sub`, `int.mul`, et `poly.eq`, `poly.lt` instanciées sur `int`.

**Hors fragment** (code de sortie 2, avec la raison) : flottants, chaînes, records, motifs alternatifs et alias, polymorphisme local, récursion mutuelle, autres primitives. Codes de sortie : 0 accepté, 1 rejeté par `typeOf`, 2 hors fragment, 3 certificat illisible.

Deux informations manquent au certificat pour décoder sans retyper : l'indice du constructeur dans un motif, et le type propriétaire d'un `construct`. Je les ajoute côté Python (annotations de la Core IR) et dans le schéma 1.0.0, encore en QA donc non publié. J'ajoute aussi `program_start` : l'indice de la première définition du programme, après le prélude.

Critère d'acceptation adapté : les exemples actuels utilisent flottants et chaînes, donc sortent du fragment (code 2, motif affiché). J'ajoute un exemple `examples/basics/certifiable.hyp` (entiers, listes, options, récursion, filtrage, fonctions polymorphes du prélude), qui doit être accepté. Un certificat altéré à la main doit être rejeté.

### user

### agent

Implémenté.

- **Côté Python** : la Core IR annote l'indice des motifs constructeurs et le type propriétaire des `construct`. Le certificat porte `program_start`, l'indice de la première définition du programme. Schéma 1.0.0 amendé (il n'était pas encore publié).
- **`formal/Hypomnesis/Certificate.lean`** : décodeur non prouvé, hors base de confiance. Il monomorphise en deux passes, instancie les types de données à la demande, traduit `match` en chaîne `case`/`fail` (type du `fail` obtenu par `typeOf`), `let rec` en `fix`, et les primitives entières et comparaisons sur `int`. Ce qui sort du fragment est signalé avec sa raison.
- **`formal/Main.lean`** : exécutable `hypomnesis-check check|eval CERTIFICAT`. Codes de sortie : 0 accepté, 1 rejeté par `typeOf`, 2 hors du fragment, 3 illisible.
- **`examples/basics/certifiable.hyp`** : variants, listes, options, récursion, filtrage, `List.map`, `filter`, `fold_left`, `length`, `hd_opt`, `max`.

Critères d'acceptation :
- l'exécutable accepte les certificats des exemples :
  - `certifiable.hyp` est **accepté** (29 définitions vérifiées après monomorphisation, 4 instances de types, 0,2 s) ;
  - `tour.hyp` et la mécanique utilisent des chaînes ou des flottants : ils sont signalés **hors fragment** (code 2), et non acceptés. Critère adapté, comme annoncé dans le plan ;
- un certificat altéré à la main est refusé : `fact 5` changé en `fact true` donne le code 1 ;
- le décodeur est séparé du noyau prouvé : seul `typeOf` décide, et le décodeur ne fait que construire des termes.

En plus : `eval` donne exactement les valeurs calculées par l'interpréteur Python (`[1; 4; 9; 16]`, 30, `[9; 10; 1]`, 10, 9, 3, `[1]`, 120). C'est un premier test différentiel, à généraliser dans HYP-028.

Branchements : 5 tests d'intégration (ignorés si l'exécutable n'est pas construit), étape dans `validate.sh lean` et `complet`, étape dans le job CI `proofs`. `./scripts/validate.sh complet` vert.

Limites, à reprendre plus tard : définitions par motif au premier niveau, récursion mutuelle, polymorphisme local, records, motifs alternatifs et alias, flottants et chaînes (HYP-021, HYP-023 et suivantes).

Passée en `qa`.

### user
