# Architecture — état d'implémentation

Ce document décrit ce qui est **implémenté** dans le dépôt. La cible complète est décrite dans
le [cahier des charges](../specification/cahier-des-charges-v0.2.md).

## Pipeline du langage

```text
source .hyp
   │  language/parser.py            Lark LALR(1) → AST de surface (language/ast.py)
   ▼
AST
   │  language/typesystem/infer.py  résolution des noms + inférence HM + élaboration
   ▼
Core IR (ir/core.py)                noms résolus, sucre éliminé, constructeurs étiquetés
   │  runtime/interpreter.py        compilation de chaque nœud en fermeture Python
   ▼
valeurs (runtime/values.py)
```

`session.py` assemble ces étapes : une `Session` charge le prélude puis des programmes
successifs ; chaque chargement étend l'environnement de types et l'environnement d'exécution.

## Choix notables

| Sujet | Implémentation |
|---|---|
| Inférence | Algorithme W, variables à niveaux (généralisation linéaire), vérification d'occurrence |
| Polymorphisme | Toutes les liaisons `let` sont généralisées (langage pur, ADR 0002) |
| Records | Nominaux ; un champ est résolu d'abord par le type connu de l'expression, sinon par portée |
| Modules | `module M = struct … end`, imbrication, `open`, chemins qualifiés `A.B.x` |
| Primitives | `external` lié à un registre fermé, vérifié statiquement (ADR 0003) |
| Récursion | Appels terminaux en pile constante (trampoline) ; récursion non terminale sur pile de 512 Mo |
| Erreurs | `ParseError`, `NameResolutionError`, `TypeCheckError`, `EvaluationError`, positionnées |
| Contrats | JSON Schema 2020-12 : enveloppe et manifeste d'extension (ADR 0004) |

## Avancement par rapport au plan (§17)

| Phase | État |
|---|---|
| 0. Fondations | ✅ dépôt, CI, ADR, contrats JSON Schema de base, Core IR spécifiée |
| 1. Langage minimal | ✅ parser, AST, HM, records, variants, modules, interpréteur, REPL |
| 2. Métamodèle épistémique | ⏳ à faire |
| 3. Plugins et JSON Schema | 🟡 registre de schémas fait ; interfaces et adaptateurs à faire |
| 4–8 | ⏳ à faire |

## Organisation

```text
src/hypomnesis/
├── language/
│   ├── grammar/hypomnesis.lark
│   ├── parser.py, ast.py, errors.py
│   └── typesystem/  types.py (termes, unification), infer.py (vérificateur-élaborateur)
├── ir/core.py
├── runtime/         values.py, natives.py, interpreter.py
├── stdlib/prelude.hyp
├── contracts/       registry.py, schemas/*.json
├── session.py
└── cli.py
```

Les autres répertoires de l'arborescence cible (§15.2) seront créés avec les phases qui les
remplissent.
