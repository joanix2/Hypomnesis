---
title: "HYP-050 · Moteur de règles avec provenance"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 4 — Raisonnement hybride · dépend de HYP-031, HYP-038"
priority: P0
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-050 · **Priorité** P0 · **Taille** L · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-031, HYP-038 · **Labels** python

#### Contexte

§5.4 et §8 : règles de déduction, par défaut, conditionnelles ; chaque conclusion porte sa provenance.

#### Tâches proposées

- Syntaxe ou bibliothèque de règles ; chaînage avant jusqu'à point fixe, avec budget.
- Règles par défaut : conclusions de support `Defaulted`, retirées si une observation les contredit.
- Intégration avec la révision (HYP-033).

#### Critères d'acceptation

- Une conclusion dérivée d'une observation et d'une estimation a le support `Estimated`.
- Le chaînage termine sous budget et le signale si le budget est atteint.

#### Fichiers concernés

- `src/hypomnesis/engine/rules.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan d'implémentation : moteur générique de chaînage avant, règles nommées
à prémisses explicites, fonction pure et condition booléenne. Contributions
de provenance conservées par règle ; les conclusions concordantes combinent
leurs justifications alternatives, les valeurs incompatibles sont signalées,
jamais sélectionnées par ordre d'insertion. Chaque évaluation consomme le
budget, et le résultat distingue point fixe et budget épuisé.

Les défauts portent leur propre source Defaulted révocable. Une observation
remplaçant un défaut retire cette source et invalide ses dépendants par
HYP-033 avant reprise du chaînage. Les mises à jour d'observations utilisent
replace_observation ; les callbacks de règles ne lancent aucun effet.
Fournir aussi un adaptateur de fonctions Hypomnesis pour que la logique M2
reste dans les DSL, pas dans le moteur Python. Les conflits logiques généraux
restent HYP-035 ; ce ticket signale les conclusions concurrentes incompatibles.

### user

### agent

Implémentation HYP-050 terminée et proposée en QA : moteur positif générique,
conditions pures, contributions par règle et alternatives de provenance,
point fixe sans réécriture du journal et budget d'évaluations exact.
Les conflits de valeurs sont explicites, y compris booléen contre entier.
Les prémisses répétées restent des produits, jamais une déduplication.

Les défauts possèdent une source révocable. Une observation de leur cible
retire cette source au prochain run et invalide puis recalcule les dépendants.
Observer une conclusion en aval ne rétracte pas les défauts de ses prémisses.
Les remplacements d'observation utilisent HYP-033.

L'adaptateur language_rule exécute une fonction Hypomnesis pure
Json.t list -> Json.t option ; exemple métier dans regles.hyp et hôte
exécutable examples/knowledge/rules.py (9600, Estimated). Aucun natif ajouté,
aucun changement de Core IR. Publication individuelle atomiquement validée ;
le passage entier n'est pas transactionnel. Une récursion de provenance peut
épuiser le budget, sans être annoncée comme point fixe.

Vérifications : 22 tests dédiés ; 89 tests ciblés règles/connaissances ;
validation complète verte (linters, types, schémas, tests moteur et Codegen,
Lean, audit des axiomes et certificat). Guides connaissances et TECHNICAL
mis à jour. Aucun sous-agent. Le passage final en done reste humain.

### user
