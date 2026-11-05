---
title: "HYP-156 · Relation runtime et sûreté du polymorphisme"
lane: todo
created: 2026-11-05T23:31:24+01:00
updated: 2026-11-05T23:31:24+01:00
description: "P1 · M · Relation des schémas polymorphes aux valeurs Core et sûreté à tout fuel"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

**Ticket** HYP-156 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020 · **Labels** lean, certification

#### Contexte

Sous-ticket de suivi de HYP-023, qui reste ouvert et conserve tous ses critères. Les preuves actuelles couvrent un fragment monomorphe et des exemples bornés ; elles ne justifient pas encore la sûreté générale d'un schéma utilisé à plusieurs types.

#### Tâches proposées

- Définir une relation de valeurs et d'environnements interprétant les schémas polymorphes aux instanciations autorisées.
- Relier cette relation à l'effacement exécuté par le véritable `Core.eval`.
- Prouver la sûreté à tout fuel du fragment polymorphe défini, sans confondre timeout/erreur explicite et sûreté.
- Ajouter les régressions d'un `let` partagé et d'une fermeture polymorphe multi-instanciée.

#### Critères d'acceptation

- La relation couvre les liaisons et fermetures pertinentes pour le rang 1, y compris une même liaison instanciée à plusieurs types.
- La sûreté du véritable `Core.eval` est prouvée pour le fragment annoncé et tout fuel ; aucune preuve ne repose sur un effacement monomorphe non justifié.
- Les théorèmes sont sans `sorry`, audités, et les régressions distinguent le théorème général des exemples concrets.

#### Fichiers concernés

- `formal/Hypomnesis/Core/PolySoundness.lean`
- `formal/Hypomnesis/Core/PolyTypes.lean`
- `formal/Hypomnesis/Audit.lean`

#### Références

- Parent : HYP-023, `.agentkanban/tasks/task_20261103_hyp023_lean-polymorphisme.md`.
- Checklist de suivi : `.agentkanban/tasks/todo_20261105_hyp023_polymorphisme-rang1.md`.
- `TECHNICAL.md`, sections polymorphisme et sûreté.

### agent

Sous-ticket borné à la relation runtime et au pont de sûreté ; les constructeurs/motifs généraux, `List.map` et le branchement CLI sont suivis séparément. HYP-023 demeure le ticket de suivi.

### user

Continuer l'implémentation de HYP-156 après le découpage des tickets.

### agent

Ajout de P49, `identity_polymorphic_let_is_safe_at_any_fuel` : le programme
concret qui lie une seule fermeture identité puis l'instancie à `int` et
`bool` est sûr à tout fuel. La preuve utilise la monotonie de `Core.eval` à
partir du résultat vérifié à fuel 20 ; si le budget est insuffisant, le
résultat `timeout` reste explicitement sûr. Le théorème est inscrit dans
`formal/Audit.lean` et `docs/verification/proprietes.md`, avec sa portée
concrète précisée dans `TECHNICAL.md`.

Cette étape ne satisfait pas encore HYP-156 : aucune relation logique générale
de valeurs/environnements polymorphes ni théorème fondamental n'a été ajouté.
`Core.ValTy` caractérise une fermeture à un seul type de flèche, tandis que
`Expr.erase` efface les variables de types en `unit`. Prouver qu'une même
fermeture est sûre à toutes ses instanciations demande donc une relation
polymorphe dédiée, pas une généralisation du pont `Core.eval_safe`.
La checklist garde ces critères ouverts ; HYP-156 reste en `todo`.

Validations réussies : `./scripts/validate.sh lean` (31 modules, audit et
vérificateur de certificats), `./scripts/validate.sh complet` (linters,
typage, tests moteur/Codegen et Lean), `kanban.py check` (124 tâches),
`graphify update .` et `git diff --check`. Aucun commit/push.

### user

### agent

Les validations finales des preuves P50 sont passées :

- `./scripts/validate.sh complet` : pre-commit, tests du moteur et de Codegen, build Lean, audit des axiomes et vérificateur de certificats réussis.
- `./scripts/validate.sh graphe` : graphe Graphify rafraîchi et validé.
- `./.venv/bin/python scripts/kanban.py check` : 124 tâches valides.
- `git diff --check` : aucune erreur.

Le ticket reste en `todo`. Le résultat prouve la sûreté du véritable `Core.eval` à tout fuel pour `PolyRuntimeFragment` et les régressions polymorphes annoncées ; il ne prouve pas le théorème fondamental pour toutes les dérivations `HasType`. La checklist conserve donc ouverte la vérification explicite de la portée d'acceptation. Aucun commit ni changement de lane.

### user

### agent

Vérification de portée : les critères propres à HYP-156 sont satisfaits dans le périmètre annoncé. P50 fournit la relation polymorphe et le théorème fondamental pour `PolyRuntimeFragment`; la régression prouve l'utilisation d'une même liaison identité à `int` et `bool`, avec sûreté du véritable `Core.eval` à tout fuel. L'audit Lean et les validations complètes sont verts. Les exclusions (notamment `fix`, constructeurs/motifs nominaux et autres formes de `HasType`) restent explicitement hors de cette garantie et demeurent suivies par HYP-023/HYP-157/HYP-158.

La checklist HYP-156 est complète. Je n'ai pas changé le champ `lane`, géré par l'extension Kanban.

### user

Commit et push du lot validé demandé.

### agent

Validation rapide réussie. `origin/main` a été actualisé : la branche locale contient 27 commits d'avance et aucun commit en retard. Le fichier mécanique sélectionné n'a aucune modification ; le lot versionné porte sur P50/HYP-156, la documentation Lean et le découpage Kanban des tickets de suivi.

### user
