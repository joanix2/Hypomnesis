---
id: HYP-064
title: "Modes simulation, dry-run et production comme handlers"
status: backlog
priority: P0
size: M
epic: P5-EFFETS
depends_on: [HYP-060, HYP-063]
labels: [python]
assignee: 
---

# HYP-064 — Modes simulation, dry-run et production comme handlers

## Contexte

§10.3 : un même programme utilise les trois modes sans modification de sa logique métier.

## Tâches

- [ ] Trois handlers de la même signature d'effets.
- [ ] Sélection du mode par la CLI ou l'application hôte, jamais par le programme.

## Critères d'acceptation

- [ ] Le même fichier source s'exécute dans les trois modes.
- [ ] En dry-run, aucun actionneur n'est appelé (vérifié sur la trace).

## Fichiers concernés

- `src/hypomnesis/effects/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
