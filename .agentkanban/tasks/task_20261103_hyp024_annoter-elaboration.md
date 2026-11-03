---
title: "HYP-024 · Pont F3a : annoter l'élaboration avec les types inférés"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T18:38:53+01:00
description: "P0 · M · Vérification formelle (Lean) · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-024 · **Priorité** P0 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-002 · **Labels** python

#### Contexte

Pour émettre un certificat (§« Pont de certificats » de `docs/verification/strategie.md`), la Core IR doit porter le type de chaque paramètre de lambda, de chaque liaison et de chaque instanciation polymorphe. Le vérificateur Python (`language/typesystem/infer.py`) les calcule déjà, mais les jette.

#### Tâches proposées

- Ajouter des annotations de types optionnelles aux nœuds `Lambda`, `Let`, `LetRec`, `Global` (instanciation) de `ir/core.py`.
- Les remplir à la fin de l'inférence, après résolution complète des variables (`prune`).
- Garantir que l'interpréteur ignore ces annotations (aucun coût à l'exécution).

#### Critères d'acceptation

- Après vérification, plus aucune annotation ne contient de variable de type non résolue (sauf variables généralisées).
- Test : chaque nœud annoté de `examples/` a un type clos ou explicitement quantifié.

#### Fichiers concernés

- `src/hypomnesis/ir/core.py`
- `src/hypomnesis/language/typesystem/infer.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan (l'utilisateur a demandé de poursuivre l'implémentation).

Ce que doit porter la Core IR pour qu'un vérificateur simple, sans inférence, puisse retyper le programme :

| Nœud | Annotation | Pourquoi |
|---|---|---|
| `Lambda` | `param_types` | le vérificateur Lean exige le type des paramètres (`lam dom body`) |
| `Let` | `forall_vars`, `value_type` | polymorphisme de `let` (abstraction de type explicite, HYP-023) |
| `LetRec` | `types`, `foralls` | `fix` exige domaine et codomaine |
| `Local`, `Global` | `type_args` | instanciation explicite du schéma de la variable |
| `Construct`, `Record` | `type_args` | `[]` ou `None` seuls ne disent pas leur paramètre de type |
| `Match` | `forall_vars` | `let (a, b) = …` généralise les variables du motif |
| `DefValue`, `DefRec`, `DefNative` | type et variables quantifiées | définitions de premier niveau |

Choix :
- les annotations sont des champs `compare=False` avec une valeur par défaut, ignorés par l'interpréteur ;
- `generalize` rend aussi la liste ordonnée des variables quantifiées (ordre = indices `TGen`), et `instantiate` les arguments créés ;
- à la fin de chaque phrase, une passe `close` remplace par `unit` les variables de type restées libres et non quantifiées. Elles viennent de sous-termes jamais contraints, comme `let _ = []` : toute instanciation est correcte, et OCaml fait le même choix ;
- une fonction `annotation_problems` vérifie l'invariant du critère d'acceptation : toute variable libre d'une annotation est liée par un quantificateur englobant.

### user

### agent

Implémenté.

- `types.py` : `generalize_vars` rend les variables quantifiées, dans l'ordre des indices `TGen` ; `instantiate_args` rend les arguments créés.
- `ir/core.py` : les annotations `param_types`, `forall_vars`, `value_type`, `types`, `foralls` et `type_args` sont posées sur `Lambda`, `Let`, `LetRec`, `Match`, `Local`, `Global`, `Construct`, `Record`, `DefValue`, `DefRec` et `DefNative`. Elles sont exclues de l'égalité et de `repr`, et l'interpréteur les ignore.
- `infer.py` remplit toutes les annotations. `let … and …` passe par des temporaires généralisés comme leur liaison, puis réinstanciés à l'identité.
- `annotations.py` :
  - `close` met à `unit` les variables jamais contraintes et non quantifiées (par exemple l'élément de `[]` dans `(fun _ -> 1) []`) ; il est appelé à la fin de chaque `check_program` ;
  - `annotation_problems` vérifie l'invariant.

Critères d'acceptation :
- après vérification, aucune variable de type libre hors d'un quantificateur englobant : vrai sur le prélude (94 définitions) et sur tous les exemples, testé ;
- chaque nœud annoté des exemples a un type clos ou explicitement quantifié : `test_prelude_and_examples_are_fully_annotated`, plus 9 tests ciblés (polymorphisme local, instanciations, `let rec`, temporaires de `and`, défaut `unit`, records).

Validation : `./scripts/validate.sh complet` entièrement vert.

Points à connaître pour HYP-025 :
- dans un groupe `let rec`, les membres se référencent avec des `type_args` vides : c'est la référence monomorphe au lieur récursif. La portée des variables est l'union des quantificateurs du groupe ;
- un `let` à motif généralise les variables du motif (`Match.forall_vars`). L'export devra soit le traduire, soit refuser ces cas tant que HYP-023 ne couvre pas le polymorphisme.

La tâche peut passer en `done` ; le changement de couloir t'appartient.

### user
