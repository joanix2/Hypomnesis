---
title: "HYP-050 · Moteur de règles avec provenance"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 4 — Raisonnement hybride · dépend de HYP-031, HYP-038"
priority: P0
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-050 · **Priorité** P0 · **Taille** L · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-031, HYP-038 · **Labels** python

#### Contexte

§5.4 et §8 : règles de déduction, par défaut, conditionnelles ; chaque conclusion porte sa provenance.

#### Tâches proposées

- Syntaxe ou bibliothèque de règles ; chaînage avant jusqu'à point fixe, avec budget.
- Règles par défaut : conclusions de support `Defaulted`, retirées si une observation les contredit.
- Intégration avec la révision (HYP-033).

#### Critères d'acceptation

- Une conclusion dérivée d'une observation et d'une estimation a le support `Estimated`.
- Le chaînage termine sous budget et le signale si le budget est atteint.

#### Fichiers concernés

- `src/hypomnesis/engine/rules.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
