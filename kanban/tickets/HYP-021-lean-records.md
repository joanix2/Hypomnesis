---
id: HYP-021
title: "Lean F1b : records et mise à jour fonctionnelle"
status: backlog
priority: P1
size: M
epic: FORMEL
depends_on: [HYP-020]
labels: [lean]
assignee: 
---

# HYP-021 — Lean F1b : records et mise à jour fonctionnelle

## Contexte

La Core IR a `Record`, `RecordUpdate`, `Field` et le motif `PRecord` ; ils ne sont pas formalisés.

## Tâches

- [ ] Ajouter les types records nominaux à Σ, ainsi que construction, accès, mise à jour et motif.
- [ ] Étendre sûreté, correction et complétude de `typeOf`.

## Critères d'acceptation

- [ ] Preuves étendues sans `sorry`.
- [ ] Un exemple `#eval` reproduit `examples/basics/tour.hyp` (`deposit`).

## Fichiers concernés

- `formal/Hypomnesis/Core/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
