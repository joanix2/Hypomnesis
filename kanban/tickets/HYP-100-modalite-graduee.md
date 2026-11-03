---
id: HYP-100
title: "Modalité graduée `[g]` dans le typeur"
status: backlog
priority: P2
size: L
epic: M3
depends_on: [HYP-031]
labels: [python]
assignee: 
---

# HYP-100 — Modalité graduée `[g]` dans le typeur

## Contexte

Étape 4 de `docs/architecture/m3-metalangage.md` (§5.3) : le support épistémique porté par les types. Une valeur `[Estimated] Length.t` combinée à `[Observed]` donne `[Estimated]` ; une action qui exige `[Observed]` refuse statiquement une estimation.

## Tâches

- [ ] Types gradués sur le treillis de support ; règles de typage (Granule, QTT) ; coercions `g ⊑ g'`.
- [ ] Interaction avec l'inférence HM : inférer les grades (contraintes de treillis).

## Critères d'acceptation

- [ ] Exemples de la note M3 §5.3 acceptés et refusés comme indiqué.
- [ ] ADR rédigée.

## Fichiers concernés

- `src/hypomnesis/language/typesystem/`

## Références

- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `kanban/README.md`
