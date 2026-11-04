---
title: "HYP-053 · Vérificateur de certificats de solveur (+ preuve Lean)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 4 — Raisonnement hybride · dépend de HYP-052"
priority: P1
tags: [certification, lean, moteur-symbolique, python, solveurs, tests, validateurs]
---

## Conversation

### user

**Ticket** HYP-053 · **Priorité** P1 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-052 · **Labels** python, lean

#### Contexte

§4.5 de `docs/architecture/m3-metalangage.md` : seul le noyau rend un fait `Derived`. Un modèle Z3 est accepté après vérification qu'il satisfait toutes les contraintes, par évaluation indépendante de Z3.

#### Tâches proposées

- Évaluateur de contraintes de la Problem IR sur une affectation.
- Lean : modéliser cet évaluateur et prouver qu'un modèle accepté satisfait les contraintes.

#### Critères d'acceptation

- Un modèle volontairement faux est refusé.
- Théorème Lean ajouté à l'audit.

#### Fichiers concernés

- `src/hypomnesis/engine/`
- `formal/Hypomnesis/Problem/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
