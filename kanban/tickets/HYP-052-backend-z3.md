---
id: HYP-052
title: "Backend Z3 depuis la Problem IR"
status: backlog
priority: P0
size: M
epic: P4-RAISONNEMENT
depends_on: [HYP-051, HYP-044]
labels: [python]
assignee: 
---

# HYP-052 — Backend Z3 depuis la Problem IR

## Contexte

Solveur initial du §15.1. Z3 n'est pas digne de confiance : il rend un certificat (modèle) vérifié ensuite.

## Tâches

- [ ] Traduire la Problem IR en Z3 (entiers, réels, booléens, contraintes linéaires).
- [ ] Rendre `sat` avec un modèle, `unsat`, ou `unknown`, avec la durée.

## Critères d'acceptation

- [ ] Le scénario MVP est résolu ; le modèle est renvoyé dans les types Hypomnesis.

## Fichiers concernés

- `src/hypomnesis/backends/z3/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
