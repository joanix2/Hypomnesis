---
id: HYP-022
title: "Lean F1c : un `match` exhaustif ne lève jamais `Match_failure`"
status: backlog
priority: P1
size: M
epic: FORMEL
depends_on: [HYP-020, HYP-010]
labels: [lean]
assignee: 
---

# HYP-022 — Lean F1c : un `match` exhaustif ne lève jamais `Match_failure`

## Contexte

Une fois l'exhaustivité implémentée côté Python (HYP-010), on prouve sa contrepartie Lean.

## Tâches

- [ ] Définir `exhaustive : Σ → Ty → List Pattern → Bool` (même algorithme que HYP-010).
- [ ] Prouver : pour une valeur bien typée, des motifs exhaustifs dont au moins un bras sans garde la couvre, le filtrage réussit.
- [ ] Corollaire : un programme dont tous les `match` sont exhaustifs ne rend jamais `matchFailure`.

## Critères d'acceptation

- [ ] Théorème prouvé et ajouté à l'audit.
- [ ] Tests croisés : Python et Lean donnent le même verdict sur un corpus.

## Fichiers concernés

- `formal/Hypomnesis/Core/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
