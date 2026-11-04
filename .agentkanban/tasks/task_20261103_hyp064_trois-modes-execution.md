---
title: "HYP-064 · Modes simulation, dry-run et production comme handlers"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-060, HYP-063"
priority: P0
tags: [effets, moteur-symbolique, python, runtime]
---

## Conversation

### user

**Ticket** HYP-064 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-060, HYP-063 · **Labels** python

#### Contexte

§10.3 : un même programme utilise les trois modes sans modification de sa logique métier.

#### Tâches proposées

- Trois handlers de la même signature d'effets.
- Sélection du mode par la CLI ou l'application hôte, jamais par le programme.

#### Critères d'acceptation

- Le même fichier source s'exécute dans les trois modes.
- En dry-run, aucun actionneur n'est appelé (vérifié sur la trace).

#### Fichiers concernés

- `src/hypomnesis/effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan d'implémentation : extraire les trois branches déjà présentes dans le
dispatcher en handlers privés de même signature, conservant tous les contrôles
communs avant leur sélection. Le mode reste fourni exclusivement par CLI ou
hôte, dry-run par défaut. Ne pas modifier le métalangage ni la logique métier.

L'exploration montre un span nommé actuator.execute autour de la validation
même en dry-run : le renommer command.dispatch et tracer actuator.execute
seulement autour du callback réellement exécuté. Tester le même fichier M1
dans les trois modes, via l'API et la CLI, ainsi que l'absence d'envoi,
de tentative et de trace d'exécution en dry-run et simulation.

### user

### agent

Les trois handlers privés partagent désormais la signature
`(actuator, outcome, move) -> None`, après les contrôles communs.
La CLI et `run_procedure` gardent le choix du mode, dry-run par défaut ;
le programme M1 ne peut pas le sélectionner.

Correction de trace : `command.dispatch` couvre les vérifications, tandis
que `actuator.execute` enveloppe seulement l'appel effectif, y compris les
relances. Il est absent en dry-run et simulation. Tests du même fichier
M1 dans les trois modes, via l'API et la CLI : états attendus, contenu
source inchangé, présence/absence du fichier produit, nombre exact d'appels,
de tentatives et de spans. Les contrôles métier/sécurité restent communs.

`./scripts/validate.sh complet` est vert : 840 tests moteur et 77 Codegen,
linters, Pyright, contrats, Kanban, Lean et audit des axiomes.
Documentation HYP-062 et TECHNICAL actualisée. Passage en QA, done réservé
à l'utilisateur.

### user
