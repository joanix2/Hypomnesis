---
id: HYP-065
title: "Lean F5a : validation et autorisation avant tout dispatch"
status: backlog
priority: P0
size: L
epic: FORMEL
depends_on: [HYP-062]
labels: [lean]
assignee: 
---

# HYP-065 — Lean F5a : validation et autorisation avant tout dispatch

## Contexte

Propriété de trace la plus importante du projet (§9.8, critères §16.4) : elle porte sur des actions physiques.

## Tâches

- [ ] Modéliser le dispatcher de HYP-062 comme système de transitions produisant une trace d'événements.
- [ ] Prouver : dans toute trace, chaque `dispatch c` est précédé de `validated c` puis `authorized c`.
- [ ] Prouver : aucun `dispatch c` sans permission accordée pour `c`.

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit et à `proprietes.md`.
- [ ] La correspondance modèle ↔ `dispatcher.py` est documentée ligne à ligne.

## Fichiers concernés

- `formal/Hypomnesis/Effects/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
