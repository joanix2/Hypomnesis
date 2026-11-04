---
title: "HYP-052 · Backend Z3 depuis la Problem IR"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 4 — Raisonnement hybride · dépend de HYP-051, HYP-044"
priority: P0
tags: [moteur-symbolique, python, solveurs]
---

## Conversation

### user

**Ticket** HYP-052 · **Priorité** P0 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-051, HYP-044 · **Labels** python

#### Contexte

Solveur initial du §15.1. Z3 n'est pas digne de confiance : il rend un certificat (modèle) vérifié ensuite.

#### Tâches proposées

- Traduire la Problem IR en Z3 (entiers, réels, booléens, contraintes linéaires).
- Rendre `sat` avec un modèle, `unsat`, ou `unknown`, avec la durée.

#### Critères d'acceptation

- Le scénario MVP est résolu ; le modèle est renvoyé dans les types Hypomnesis.

#### Fichiers concernés

- `src/hypomnesis/backends/z3/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
