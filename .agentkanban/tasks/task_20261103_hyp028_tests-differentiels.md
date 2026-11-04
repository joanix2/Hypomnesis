---
title: "HYP-028 · Tests différentiels interpréteur Python ↔ sémantique Lean"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Vérification formelle (Lean) · dépend de HYP-026"
priority: P1
tags: [certification, compilateur, lean, metalangage, python, runtime, tests]
---

## Conversation

### user

**Ticket** HYP-028 · **Priorité** P1 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-026 · **Labels** python, lean, tests

#### Contexte

La fidélité de l'interpréteur Python à la sémantique prouvée n'est couverte que par des tests (`docs/verification/strategie.md`).

#### Tâches proposées

- Générateur Hypothesis de termes bien typés du fragment (génération dirigée par les types).
- Exécuter chaque terme en Python et avec `hypomnesis-check eval` ; comparer valeurs, `timeout` et `matchFailure`.
- Rendre le budget comparable des deux côtés (même notion de pas, ou comparaison des seuls résultats terminés).

#### Critères d'acceptation

- Au moins 500 termes par exécution de CI, aucune divergence.
- Une divergence introduite volontairement dans l'interpréteur Python est détectée.

#### Fichiers concernés

- `tests/differential/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan Mac approuvé, exécution séquentielle sans sous-agents. La validation
complète de départ est verte à f35b5e0. HYP-026 est en QA, donc le prérequis
est acquis. Checklist créée avant implémentation.

Approche : génération dirigée par types de sources fermées du fragment,
élaboration réelle, export du même IR exécuté en Python et évaluation Lean.
Comparer exactement les données et erreurs terminées. Les budgets Lean
et la trampoline Python ne comptent pas les mêmes pas : un timeout Lean
ne sera jamais assimilé à une égalité de résultats. Le corpus généré est
borné et doit terminer dans un budget explicite ; un test dédié vérifie
l'épuisement d'un petit budget puis la même exécution avec budget suffisant.
La CI des preuves exigera le binaire et affichera les statistiques Hypothesis.

### user

### agent

Implémentation réalisée dans tests/differential : génération fermée dirigée
par sept types observables, variables liées, captures, applications,
récursion bornée, filtrage, gardes, alternatives, records et comparaisons
binary64. Annotations explicites pour ne pas générer par accident du
polymorphisme local hors fragment ; comparaisons natives seulement aux
types pris en charge par le catalogue Lean.

Le comparateur exige l'égalité exacte des valeurs structurées ou erreurs
terminées. Les 500 termes générés passent, plus les exemples explicites
et douze régressions. La mutation réelle de _c_Literal est détectée.
Un budget Lean insuffisant est refusé comme résultat non comparable,
puis le même programme est vérifié avec un budget suffisant.
Absence du checker sous HYPOMNESIS_REQUIRE_LEAN=1 testée comme échec,
pas comme skip. CI et validateur lean/complet branchés.

Validation complète verte : linters, types, schémas, suites moteur/Codegen,
build/audit Lean et 68 tests checker/différentiel. Statistiques du passage
obligatoire : 500 passing, 0 failing, arrêt à max_examples=500.
Documentation technique et stratégie actualisées, aucune sémantique
runtime ni Core IR modifiée. Passage en QA, done réservé à l'utilisateur.

### user
