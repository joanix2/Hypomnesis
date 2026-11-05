---
title: "HYP-023 · Lean F2 : polymorphisme dans les termes élaborés"
lane: doing
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-020"
priority: P1
tags: [certification, lean, metalangage]
---

## Conversation

### user

Périmètre global confirmé : keep-local-and-gates.

### agent

Le jalon des environnements de schémas est committé localement en
`9bc234e` (sans push). `validate.sh lean`, `validate.sh rapide`,
`validate.sh graphe` et `kanban.py check` passent ; le worktree est propre.
Le ticket reste en cours : les termes polymorphes, leur sûreté et le
branchement du vérificateur ne sont pas encore implémentés.

### user

Reprise après approbation du plan global de clôture des P1. Continuer
HYP-023 depuis le jalon e7271e6, sans sous-agent ni push.

### agent

Itération 3 ajoutée dans `Core/PolyTypes.lean` : contextes de variables
représentés par des schémas, instanciation indexée, conservation de portée,
et commutation de la substitution avec l'instanciation. Les régressions
couvrent `List.map` instancié à int/bool, l'arité invalide et une variable
de type extérieure. P40, l'audit d'axiomes et la documentation sont mis à
jour. `lake build` et l'audit Lean passent avec les seuls axiomes standard.

Cette étape ne type toujours pas les termes polymorphes, ne modifie pas
`Core.typeOf` ou le décodeur, et ne vérifie pas le corps du véritable
`List.map`. HYP-023 reste `doing` ; prochaine étape : termes et jugement de
typage, puis sûreté et branchement.

### user

**Ticket** HYP-023 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-020 · **Labels** lean

#### Contexte

L'inférence HM produit des schémas `∀ᾱ.τ`. Pour que le certificat reste vérifiable par un algorithme simple, il doit expliciter les abstractions et instanciations de types, à la manière de Système F restreint au rang 1 : on ne prouve pas l'algorithme W, on vérifie son résultat.

#### Tâches proposées

- Ajouter variables de type, `Λ` (généralisation au `let`) et instanciation explicite aux termes élaborés.
- Substitution de types et lemmes associés (préservation du typage par substitution).
- Étendre la sûreté, `typeOf` et ses preuves.

#### Critères d'acceptation

- Preuves sans `sorry`.
- `List.map` du prélude s'exprime et se type dans le fragment.

#### Fichiers concernés

- `formal/Hypomnesis/Core/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan P1 approuvé. Inventaire initial : `Ty`, `Sig`, `HasType`, `typeOf`
et les certificats sont actuellement monomorphes. Le véritable `List.map`
du prélude dépend de `rev` et `fold_left` ; prouver seulement une autre
fonction map isolée ne satisfait pas le jalon. L'extension doit traiter
les signatures de données paramétriques et réparer les preuves de
filtrage/records/fuel couplées ; aucun changement partiel du noyau effectué.

L'ordre du lot est ajusté pour livrer d'abord la chaîne indépendante
d'observabilité HYP-070–073, sans faire dépendre ces tickets de HYP-023.
HYP-023 reste à implémenter ; aucune monomorphisation présentée comme
preuve du polymorphisme, aucun passage en QA.

### user

Suite du lot P1 : polymorphisme avant les services. Plan approuvé.

### agent

Implémentation séquentielle du plan approuvé, sans sous-agent et sans push.
Checklist dédiée créée. Rang 1 : schémas au let, arguments de fonctions et
récursion monomorphes ; les variables de types liées utilisent des indices
de de Bruijn. Les signatures nominales portent leurs arités et leurs
arguments de constructeurs paramétriques.

Première étape dans Core/PolyTypes : algèbre des types et schémas,
renommage/substitution, protection des variables liées, vérification de
portée et instanciation contrôlée par arité. Le noyau monomorphe et son
checker public restent intacts jusqu'au branchement vérifié.
Ce module préparatoire n'est pas un interpréteur de remplacement ; il ne
satisfait pas à lui seul HYP-023. Le schéma de type de map sert de régression
de représentation et n'est pas présenté comme preuve du corps du prélude.

### user

### agent

Fondations implémentées et compilées dans `Core/PolyTypes.lean` :
monotypes ouverts, schémas, données nominales avec arguments de types et
arités déclarées. Preuves d'identité/composition des substitutions et
renommages, substitution sous quantificateurs sans capture, conservation
des portées, commutation substitution/instanciation et bonne portée des
types de constructeurs instanciés. L'inclusion des types historiques est
invariante par substitution ; ce n'est pas encore un pont des programmes.

Douze régressions calculées dans `Core/PolyTypeExamples.lean` :
signature de liste générique, schéma de map et instanciation int/bool,
arguments génériques, mauvaise arité, indices libres, données/constructeurs
inconnus, déclaration mal scopée, protection des variables liées et
conservation du contexte extérieur. Aucun programme map de remplacement.

`lake build` et l'audit compilent toutes les preuves existantes avec ces
nouveaux modules. Les vingt énoncés additionnels audités n'utilisent que
les axiomes standard autorisés. ADR 0020, catalogue P36–P39, stratégie et
document technique explicitent les limites. Le décodeur et le CLI restent
inchangés ; typage des termes et sûreté polymorphe restent à faire.
HYP-023 demeure doing. Validation du jalon avant commit en cours.

### user

### agent

Jalon des fondations validé : contrôles ciblés pre-commit, `validate.sh lean`,
`validate.sh rapide` et `validate.sh graphe` verts. La suite Lean comprend
les certificats et 500 cas différentiels générés, sans échec. Treize
régressions de types compilent (rectification du compte de douze ci-dessus).

Commit local de ce jalon, sans push. La suite du plan reste le typage
des termes polymorphes et des environnements, la sûreté, les preuves
couplées puis le branchement du véritable checker. HYP-023 n'est ni en
QA ni terminé ; aucune certification générique du corps de List.map
n'est encore annoncée.

### user
