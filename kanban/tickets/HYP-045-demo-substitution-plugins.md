---
id: HYP-045
title: "Démonstration : deux plugins derrière la même interface"
status: backlog
priority: P1
size: S
epic: P3-EXTENSIONS
depends_on: [HYP-044]
labels: [python, exemple]
assignee: 
---

# HYP-045 — Démonstration : deux plugins derrière la même interface

## Contexte

Critère d'acceptation du §16.4 et hypothèse H6.

## Tâches

- [ ] Deux estimateurs d'épaisseur (règle simple, régression) derrière la même interface.
- [ ] Le même programme fonctionne avec l'un ou l'autre, sur simple changement de configuration.

## Critères d'acceptation

- [ ] Test d'intégration qui exécute le programme avec chaque plugin sans modifier le source.

## Fichiers concernés

- `examples/mechanics/`
- `tests/integration/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
