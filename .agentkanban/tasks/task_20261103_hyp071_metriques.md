---
title: "HYP-071 · Métriques du §12.4"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 6 — Observabilité · dépend de HYP-070"
priority: P1
tags: [observabilite, outillage, python]
---

## Conversation

### user

**Ticket** HYP-071 · **Priorité** P1 · **Taille** M · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-070 · **Labels** python, observabilité

#### Contexte

Tableau des métriques du §12.4 ; labels sans identifiants à forte cardinalité.

#### Tâches proposées

- Compteurs et histogrammes listés ; export OTLP.
- Test qui refuse un label de métrique contenant un identifiant de message, de trace ou de connaissance.

#### Critères d'acceptation

- Toutes les métriques du §12.4 sont émises par le scénario MVP.

#### Fichiers concernés

- `src/hypomnesis/observability/metrics.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
