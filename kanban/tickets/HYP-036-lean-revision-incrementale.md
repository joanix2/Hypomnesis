---
id: HYP-036
title: "Lean F4a : révision incrémentale = recalcul complet"
status: backlog
priority: P1
size: L
epic: FORMEL
depends_on: [HYP-033, HYP-003]
labels: [lean]
assignee: 
---

# HYP-036 — Lean F4a : révision incrémentale = recalcul complet

## Contexte

Prouver sur un modèle du moteur que l'algorithme de HYP-033 est exact, et que le journal n'est jamais détruit.

## Tâches

- [ ] Modéliser l'état (faits, provenances, index inverse) et l'opération de révision incrémentale.
- [ ] Prouver : `revise_incr s x = recompute (retract s x)`.
- [ ] Prouver : le journal après révision étend le journal précédent (préfixe).

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit et à `proprietes.md` (lot F4).

## Fichiers concernés

- `formal/Hypomnesis/Epistemics/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
