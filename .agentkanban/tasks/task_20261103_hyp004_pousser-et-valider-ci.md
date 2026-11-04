---
title: "HYP-004 · Pousser la branche et valider la CI (Python et preuves)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · S · Fondations et gouvernance · dépend de HYP-003"
priority: P0
tags: [ci, humain, mvp, outillage]
---

## Conversation

### user

**Ticket** HYP-004 · **Priorité** P0 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-003 · **Labels** humain, ci

> **Décision humaine requise** : ce ticket ne doit pas être réalisé par un agent seul.

#### Contexte

La branche `phase-0-1-langage-minimal` n'a jamais été poussée : le workflow `.github/workflows/ci.yml` (jobs `test` et `proofs`) n'a donc jamais tourné sur GitHub. Le job `proofs` installe elan et lance `lake build`.

#### Tâches proposées

- Pousser la branche vers `origin` (décision humaine).
- Observer les deux jobs ; corriger ce qui échoue (versions Python 3.11/3.13, installation d'elan, cache).

#### Critères d'acceptation

- Les jobs `test` et `proofs` sont verts sur la branche.
- Le job `proofs` échoue si l'on introduit volontairement un `sorry` (vérifié une fois puis annulé).

#### Fichiers concernés

- `.github/workflows/ci.yml`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

L'utilisateur autorise explicitement HYP-004 avec HYP-007 et HYP-144.
Le contexte initial est dépassé : la branche a déjà été fusionnée et publiée sur `main`.
La CI du commit courant `7d89099dad877e49586b65653e359bbab5ee35c5`
est verte : [exécution 41859533221](https://github.com/joanix2/Hypomnesis/actions/runs/41859533221),
jobs `test (3.11)`, `test (3.12)`, `test (3.13)` et `proofs` tous terminés en succès.

Plan et checklist : conserver ce fonctionnement et tester la commande exacte de l'étape
`Reject sorry` dans un dossier temporaire isolé. Preuve valide : code 0 ; insertion
de `sorry` : code 1 ; insertion de `admit` : code 1 ; restauration : code 0.
Ce contrôle est exécuté localement et ajouté à la suite de tests ; aucune preuve invalide
n'est publiée et aucun échec distant volontaire n'est revendiqué.

### user

### agent

Validation complète verte sur les changements : 652 tests, linters, types, schémas,
Kanban, compilation Lean, audit et vérification de certificats. Les trois cas de
non-régression du garde-fou CI passent dans `tests/tools/test_ci.py`.
Les quatre jobs distants sont verts sur le commit publié indiqué ci-dessus ;
le test négatif a été effectué sur la commande CI exacte, localement et sans publication
de `sorry`. Les changements de ce lot ne sont pas encore publiés.
Checklist complétée ; couloir laissé à l'utilisateur.

### user

### agent

Validation finale après ajout des tests d'orchestration Graphify : 655 tests et
`validate.sh complet` verts. La CI distante citée reste celle du commit antérieur publié ;
aucune nouvelle exécution distante ni publication de ce lot n'est revendiquée.

### user
