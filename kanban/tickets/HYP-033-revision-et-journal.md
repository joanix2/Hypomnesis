---
id: HYP-033
title: "Révision des connaissances et journal d'événements"
status: backlog
priority: P0
size: M
epic: P2-EPISTEMIQUE
depends_on: [HYP-031]
labels: [python]
assignee: 
---

# HYP-033 — Révision des connaissances et journal d'événements

## Contexte

§7.3 : identifier les dépendants, invalider, recalculer, conserver l'historique, signaler les contradictions. Avec la provenance en semi-anneau, retirer une observation revient à la substitution `x ↦ 0` (P10, P11).

## Tâches

- [ ] Journal en ajout seul : `Observed`, `Retracted`, `Replaced`, `Derived`, `Revised`.
- [ ] Index inverse observation → conclusions (variables des termes de provenance).
- [ ] Révision incrémentale : recalculer uniquement les conclusions qui mentionnent l'observation.

## Critères d'acceptation

- [ ] Test : révision incrémentale et recalcul complet donnent le même état (sur des scénarios générés).
- [ ] Aucune entrée du journal n'est jamais modifiée ni supprimée.

## Fichiers concernés

- `src/hypomnesis/epistemics/revision.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
