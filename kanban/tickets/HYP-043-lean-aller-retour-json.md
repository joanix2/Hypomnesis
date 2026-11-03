---
id: HYP-043
title: "Lean F5d : aller-retour JSON et conformité au schéma"
status: backlog
priority: P1
size: L
epic: FORMEL
depends_on: [HYP-042, HYP-021]
labels: [lean]
assignee: 
---

# HYP-043 — Lean F5d : aller-retour JSON et conformité au schéma

## Contexte

Contrepartie prouvée de HYP-042, pour le fragment de types formalisé.

## Tâches

- [ ] Modéliser JSON et un sous-ensemble de JSON Schema (types, propriétés requises, `additionalProperties: false`).
- [ ] Prouver : `decode (encode v) = some v` et `ValTy v t → conforms (encode v) (schemaOf t)`.

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/Contracts/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
