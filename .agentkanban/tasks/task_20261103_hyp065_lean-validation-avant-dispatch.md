---
title: "HYP-065 · Lean F5a : validation et autorisation avant tout dispatch"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Vérification formelle (Lean) · dépend de HYP-062"
priority: P0
tags: [contrats, effets, lean, moteur-symbolique, securite, validateurs]
---

## Conversation

### user

**Ticket** HYP-065 · **Priorité** P0 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-062 · **Labels** lean

#### Contexte

Propriété de trace la plus importante du projet (§9.8, critères §16.4) : elle porte sur des actions physiques.

#### Tâches proposées

- Modéliser le dispatcher de HYP-062 comme système de transitions produisant une trace d'événements.
- Prouver : dans toute trace, chaque `dispatch c` est précédé de `validated c` puis `authorized c`.
- Prouver : aucun `dispatch c` sans permission accordée pour `c`.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit et à `proprietes.md`.
- La correspondance modèle ↔ `dispatcher.py` est documentée ligne à ligne.

#### Fichiers concernés

- `formal/Hypomnesis/Effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan : formaliser l'automate complet des états Python et les journaux
par identifiant de commande (ordre inversé dans Lean). Une transition vers
Authorized exige la permission hôte ; aucune autre transition ne la fabrique.
Prouver l'ordre pour chaque occurrence de Dispatched, y compris les relances,
et l'impossibilité d'un dispatch si la permission est refusée.

Le modèle est une surapproximation du dispatcher séquentiel : autorise toutes
les transitions de la table, même les relances que Python borne davantage.
Il ne prétend pas prouver jsonschema, les callbacks hôte, la réalité physique,
la fidélité automatique du Python ni l'absence de mutation par un hôte hostile.
Documenter chaque bloc de contrôle Python avec ses lignes et sa relation au
modèle, ajouter audit, catalogue et tests de correspondance des tables.

### user

### agent

Preuves compilées dans `formal/Hypomnesis/Effects/Dispatch.lean` :
`dispatch_ordered` quantifie chaque occurrence de dispatch, relances comprises,
et retrouve validation puis autorisation dans son passé ;
`dispatch_permitted` et `no_dispatch_without_permission` établissent la
permission nécessaire. Les trois théorèmes dépendent seulement de propext,
sans axiome métier, et sont inclus dans Audit.lean et le catalogue P17/P18.

La correspondance avec dispatcher.py est détaillée bloc par bloc et ligne
par ligne dans `docs/verification/dispatch.md`. Le test exécute Lean pour
comparer les 144 paires d'états à Python ; aucune comparaison ignorée si
Lean manque. La liste exportée est elle-même prouvée exhaustive en Lean.

Limite explicite : preuve du modèle de traces par commande sous permission
hôte, avec correspondance Python testée/documentée ; ce n'est pas une preuve
de raffinement du Python, des callbacks, de la concurrence ou du matériel.

`./scripts/validate.sh complet` est vert : 841 tests moteur, 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes.
Passage en QA ; done reste une décision humaine.

### user
