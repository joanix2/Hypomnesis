---
title: "HYP-033 · Révision des connaissances et journal d'événements"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 2 — Moteur épistémique · dépend de HYP-031"
---

## Conversation

### user

**Ticket** HYP-033 · **Priorité** P0 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-031 · **Labels** python

#### Contexte

§7.3 : identifier les dépendants, invalider, recalculer, conserver l'historique, signaler les contradictions. Avec la provenance en semi-anneau, retirer une observation revient à la substitution `x ↦ 0` (P10, P11).

#### Tâches proposées

- Journal en ajout seul : `Observed`, `Retracted`, `Replaced`, `Derived`, `Revised`.
- Index inverse observation → conclusions (variables des termes de provenance).
- Révision incrémentale : recalculer uniquement les conclusions qui mentionnent l'observation.

#### Critères d'acceptation

- Test : révision incrémentale et recalcul complet donnent le même état (sur des scénarios générés).
- Aucune entrée du journal n'est jamais modifiée ni supprimée.

#### Fichiers concernés

- `src/hypomnesis/epistemics/revision.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
