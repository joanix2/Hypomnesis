---
id: HYP-037
title: "Lean F4b : pas de faux conflit"
status: backlog
priority: P2
size: M
epic: FORMEL
depends_on: [HYP-035, HYP-036]
labels: [lean]
assignee: 
---

# HYP-037 — Lean F4b : pas de faux conflit

## Contexte

Si le moteur signale `Conflict`, l'incompatibilité est réellement dérivable des faits courants.

## Tâches

- [ ] Modéliser la détection de HYP-035 ; prouver sa correction (et sa complétude si elle est visée).

## Critères d'acceptation

- [ ] Théorème sans `sorry`, ajouté à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/Epistemics/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
