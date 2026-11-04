---
title: "HYP-010 · Vérifier l'exhaustivité et la redondance du filtrage"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Langage · dépend de HYP-002"
priority: P1
tags: [compilateur, metalangage, python, tests]
---

## Conversation

### user

**Ticket** HYP-010 · **Priorité** P1 · **Taille** M · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python

#### Contexte

Aujourd'hui un `match` non exhaustif n'est détecté qu'à l'exécution (`Match_failure`). Le vérificateur connaît tous les constructeurs de chaque type et peut décider l'exhaustivité (algorithme de Maranget, « Warnings for pattern matching », JFP 2007).

#### Tâches proposées

- Implémenter l'analyse sur les motifs de la Core IR (constructeurs, tuples, records, littéraux, alternatives).
- Émettre un avertissement positionné avec un exemple de valeur non couverte ; signaler les bras inaccessibles.
- Ajouter une option `--strict` à la CLI qui transforme les avertissements en erreurs.
- Introduire un canal d'avertissements dans `CheckResult` (il n'existe pas encore).

#### Critères d'acceptation

- `match x with Some y -> y` produit un avertissement citant `None`.
- Aucun avertissement sur le prélude ni sur les exemples.
- Tests unitaires couvrant variants imbriqués, listes, littéraux et gardes (une garde rend le bras non couvrant).

#### Fichiers concernés

- `src/hypomnesis/language/typesystem/`
- `src/hypomnesis/cli.py`
- `tests/unit/`

#### Références

- `docs/language/reference.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan/checklist : analyse de matrices de motifs élaborés, après unification,
par spécialisation des constructeurs et matrice par défaut (Maranget).
Couverture et utilité des bras sont distinctes : une garde ne couvre pas
les bras suivants, même si son expression est constante. Les motifs de
paramètres et de liaisons doivent aussi être analysés.

Conserver les avertissements dans CheckResult/LoadResult et la session,
avec position et fichier, sans changer l'évaluation ni la Core IR.
Réutiliser le schéma diagnostics 1.0, qui admet déjà warning. CLI check
--strict refuse ces avertissements avant export/certification ; CLI
normale et LSP les affichent sans transformer tout programme partiel
en erreur. Tester prélude/exemples et programmes M2/M1 sans adaptateurs.
La preuve Lean de l'analyse reste HYP-022, pas une promesse de ce ticket.

### user

### agent

Analyse implémentée sur les motifs Core IR, après unification : matrices
spécialisées et défaut, variants imbriqués, listes, produits/records
partiels, littéraux, alternatives et alias. Les gardes ne couvrent jamais
les bras suivants. Matches, fonctions, paramètres et liaisons sont suivis.
Les champs répétés d'un motif de record sont refusés : les rabattre dans
un dictionnaire masquerait un motif contradictoire pendant l'analyse.

CheckResult/LoadResult portent les avertissements ; la session conserve
leur historique de typage et les fichiers des couches M2. CLI texte/JSON,
REPL et LSP remontent les diagnostics. check --strict refuse avec code 1
avant export/certification, sans changer l'évaluation ni la Core IR.
Le schéma diagnostics 1.0 admettait déjà warning : pas de version modifiée.

141 tests ciblés verts ; 80 matrices booléennes générées sont comparées à
l'intégralité de leur domaine réel d'exécution. Prélude et six exemples
sans avertissement. Test supplémentaire contre le vrai serveur LSP en
stdio : gravité 2, correction effaçant le diagnostic, puis bras inaccessible.
Validation complète verte, types et audit inclus ; les 500 termes
différentiels et les 86 tests Lean obligatoires passent toujours.

Limites documentées : pas de preuve des gardes ni d'inhabitabilité d'un
type récursif sans constructeur de base ; témoin `_` symbolique.
La preuve Lean de l'analyse reste HYP-022. QA proposée à l'humain.

### user

### agent

Validation rapide finale et graphe verts, test LSP stdio supplémentaire
inclus dans la suite complète de régression avant commit. Aucun push.

### user
