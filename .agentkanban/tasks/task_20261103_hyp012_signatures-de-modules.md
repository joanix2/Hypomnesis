---
title: "HYP-012 · Signatures de modules (`module type`, contrainte `M : S`)"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Langage · dépend de HYP-002"
priority: P1
tags: [compilateur, metalangage, python]
---

## Conversation

### user

**Ticket** HYP-012 · **Priorité** P1 · **Taille** L · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python

#### Contexte

Les signatures de modules sont le point d'entrée des théories du niveau M3 (§4.1 de `docs/architecture/m3-metalangage.md` : « une signature de module est déjà une théorie sans équations »). Elles sont aussi nécessaires pour typer statiquement les interfaces d'extensions (§13.2).

#### Tâches proposées

- Grammaire : `module type S = sig val f : t  type t ... end` et `module M : S = struct ... end`.
- Types abstraits dans les signatures (`type t` sans définition) : rendre `M.t` abstrait hors du module.
- Vérifier qu'une structure satisfait une signature (sous-typage de signatures, ordre des champs libre).

#### Critères d'acceptation

- Un module qui n'implémente pas une valeur de sa signature est rejeté, avec un message positionné.
- Un type abstrait ne peut pas être déconstruit hors du module.
- La référence du langage est mise à jour.

#### Fichiers concernés

- `src/hypomnesis/language/grammar/hypomnesis.lark`
- `src/hypomnesis/language/typesystem/infer.py`
- `docs/language/reference.md`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan / todo / implement du lot Mac approuvé ; démarrage après HYP-011,
validé et committé localement (9c2fe06), sans push.

Arbitrage confirmé : `module type S = sig ... end` et
`module M : S = struct ... end`, scellement opaque. `type t` cache la
représentation ; `type t = float` conserve explicitement cette égalité.
L'ordre des spécifications est libre, les membres supplémentaires disparaissent
de l'interface publique. Les signatures sont lexicales et peuvent être
importées ; aucun foncteur ni adoption de HYP-046.

Implémentation prévue : spécifications de types abstraits/alias manifestes
et de valeurs ; vérification par instanciation rigide pour ne pas accepter
une fonction monomorphe comme polymorphe ; identités abstraites fraîches
par module et ponts Core explicites pour les valeurs exportées. Les corps
gardent leur environnement privé et leurs représentations concrètes.
Contrats JSON : refus explicite d'un type opaque sans représentation publique.
Catalogue et diagnostics : uniquement les exports visibles.

Les certificats conservent le format Core existant : l'export abaisse les
types abstraits vers leurs représentations pour le checker Lean. Cela vérifie
le programme élaboré, pas une nouvelle preuve Lean du scellement ou du
frontend. Cette frontière sera documentée et testée avec le vrai vérificateur.
Tests positifs/négatifs, imports/LSP/catalogue/contrats, coloration et hôte
réel, puis complet/rapide/graphe avant QA et commit local.

### user

### agent

HYP-012 implémenté et validation complète verte. Signatures lexicales et
importables, spécifications de types abstraits/alias manifestes et de valeurs,
ordre libre, types paramétrés, scellement génératif et exports restreints.
Les signatures promises sont vérifiées par instanciation rigide ; une fonction
monomorphe ne peut pas usurper un contrat polymorphe.

L'interface publique est distincte de l'implémentation privée, pas un simple
masquage des constructeurs. Les tests refusent aussi la déconstruction avec
des constructeurs ou champs de représentation connus par un autre module,
le mélange de deux types abstraits distincts et les coercitions implicites.
Les alias d'import gardent la même identité. Une erreur laisse l'environnement
antérieur intact ; les collisions de signatures entre couches sont refusées.

Les contrats JSON des types opaques sont explicitement refusés. Catalogue,
descriptions M2 et sorties CLI masquent les membres et représentations privés.
Les programmes restent statiquement vérifiables dans le LSP avec overlays
transitifs, sans exécution.

35 cas dédiés, tests CLI/LSP/contrats/catalogue et cinq programmes réellement
acceptés puis évalués par Lean (scalaires, variants, records, abstraction
imbriquée, types paramétrés et spécialisation polymorphe). Le certificat
1.1.0 abaisse les représentations ; ni nouvelle IR, ni nouvelle sémantique,
ni preuve revendiquée du scellement Python. ADR 0018, référence et documentation
technique mises à jour.

13 tests TextMate et hôte VS Code réel verts, avec diagnostic d'abstraction
invalide puis correction. Extension 0.1.4 construite, installée, grammaire
installée comparée à la source. Validation complète verte : linters, types,
schémas, tests noyau et Codegen, Lean et audit des axiomes.
Passage en QA, done reste humain ; rapide/graphe avant commit local,
aucun push. HYP-022 et HYP-023 restent à réaliser dans le lot.

### user
