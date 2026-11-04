---
title: "TODO HYP-148 · Ordonnanceur parallèle"
lane: qa
created: 2026-11-04T18:22:06+01:00
updated: 2026-11-04T18:22:06+01:00
description: "CLI locale et tests sur dépôts Git temporaires"
priority: P1
tags: [git, kanban, outillage, tests]
---

# Itération 1

- [x] Sélectionner les tickets prêts avec priorités et conflits conservateurs.
- [x] Préparer branches, worktrees et missions sans écraser d'existant.
- [x] Persister état et validations par SHA, verrouiller et reprendre après interruption.
- [x] Intégrer séquentiellement avec validation et arrêt sur échec/conflit.
- [x] Tester cas heureux, refus, concurrence, reprise et échecs dans des dépôts temporaires.
- [x] Documenter la CLI, valider Ruff/Pyright et validation complète.
