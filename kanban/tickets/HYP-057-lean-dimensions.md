---
id: HYP-057
title: "Lean F6 : cohérence dimensionnelle et invariance d'échelle"
status: backlog
priority: P2
size: L
epic: FORMEL
depends_on: [HYP-056, HYP-023]
labels: [lean]
assignee: 
---

# HYP-057 — Lean F6 : cohérence dimensionnelle et invariance d'échelle

## Contexte

Paramétricité des unités (Kennedy, POPL 1997) : une fonction polymorphe en dimension commute avec le changement d'échelle.

## Tâches

- [ ] Formaliser les types dimensionnels du fragment.
- [ ] Prouver la sûreté et le théorème d'invariance par changement d'unités (relation logique).

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/Dimensions/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
