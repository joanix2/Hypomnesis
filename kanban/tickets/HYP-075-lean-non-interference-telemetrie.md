---
id: HYP-075
title: "Lean : la télémétrie n'influe pas sur les résultats"
status: backlog
priority: P3
size: M
epic: FORMEL
depends_on: [HYP-070, HYP-036]
labels: [lean]
assignee: 
---

# HYP-075 — Lean : la télémétrie n'influe pas sur les résultats

## Contexte

ADR 0005 et §12.8 : la provenance et l'observabilité restent distinctes.

## Tâches

- [ ] Modéliser l'exécution instrumentée comme une exécution enrichie d'émissions de télémétrie.
- [ ] Prouver que la projection sur les résultats est identique à l'exécution non instrumentée.

## Critères d'acceptation

- [ ] Théorème sans `sorry`, ajouté à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
