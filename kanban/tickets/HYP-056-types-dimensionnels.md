---
id: HYP-056
title: "Types dimensionnels (unification modulo groupe abélien)"
status: backlog
priority: P2
size: L
epic: P4-RAISONNEMENT
depends_on: [HYP-002]
labels: [python]
assignee: 
---

# HYP-056 — Types dimensionnels (unification modulo groupe abélien)

## Contexte

§5.3 et §6.5 de `docs/architecture/m3-metalangage.md`. Les dimensions forment un groupe abélien libre ; l'unification modulo AG est décidable (Kennedy, ESOP 1994). Le noyau ne doit connaître aucune unité : la théorie est déclarée par une bibliothèque.

## Tâches

- [ ] Types indexés par dimension (`float<m/s>`), inférence avec unification AG.
- [ ] Bibliothèque `Units` déclarant dimensions de base et conversions.
- [ ] Réécrire `examples/mechanics/units.hyp` avec ces types.

## Critères d'acceptation

- [ ] `m + s` refusé ; `m / s * s` accepté comme `m` ; types principaux inférés.
- [ ] ADR rédigée.

## Fichiers concernés

- `src/hypomnesis/language/typesystem/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
