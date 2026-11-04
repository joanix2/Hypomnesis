---
title: "HYP-051 · Problem IR : variables, domaines, contraintes, objectifs"
lane: doing
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-04T18:22:06+01:00
description: "P0 · M · Phase 4 — Raisonnement hybride · dépend de HYP-002"
priority: P0
tags: [moteur-symbolique, python, solveurs]
---

## Conversation

### user

**Ticket** HYP-051 · **Priorité** P0 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§13.3 : Problem IR (variables, domaines, contraintes, objectifs, états, actions, transitions).

#### Tâches proposées

- `ir/problem.py` : structures immuables ; construction depuis le langage.
- Sérialisation JSON avec schéma versionné.

#### Critères d'acceptation

- La contrainte du scénario MVP (épaisseur dans une plage, rigidité) s'exprime en Problem IR.

#### Fichiers concernés

- `src/hypomnesis/ir/problem.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Plan parallèle approuvé : compléter la Problem IR et son pont déjà présents,
sans réécrire le backend Z3 ni développer de nouveau solveur. Ajouter des états,
actions et transitions déclaratifs, une validation stricte et un JSON versionné
exact, y compris rationnels et grands entiers. Maintenir les consommateurs et
la construction typée depuis `.hyp`, sans modifier la Core IR ni le runtime.

Surfaces réservées : `ir/problem.py`, `engine/bridge.py`, déclarations Problem
du prélude si nécessaires, schéma et tests spécifiques,
`docs/architecture/problem-ir.md`. Pas de nouveau natif partagé sans coordination.
Le coordinateur conserve les tickets, checklists et documents centraux.
Trois worktrees isolés, intégration séquentielle validée, aucun push.

### user
