---
id: HYP-067
title: "Lean F5c : dry-run sans dispatch, même terme dans les trois modes"
status: backlog
priority: P1
size: M
epic: FORMEL
depends_on: [HYP-064, HYP-065]
labels: [lean]
assignee: 
---

# HYP-067 — Lean F5c : dry-run sans dispatch, même terme dans les trois modes

## Contexte

§10.3 : la logique métier ne dépend pas du mode.

## Tâches

- [ ] Prouver : le handler dry-run ne produit aucun `dispatch`.
- [ ] Prouver : les trois handlers interprètent le même terme ; la simulation et la production ne diffèrent que par les réponses des opérations.

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/Effects/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
