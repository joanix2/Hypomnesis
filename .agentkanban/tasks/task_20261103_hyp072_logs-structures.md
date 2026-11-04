---
title: "HYP-072 · Logs structurés corrélés et expurgation"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · S · Phase 6 — Observabilité · dépend de HYP-070"
priority: P1
tags: [observabilite, outillage, python, securite]
---

## Conversation

### user

**Ticket** HYP-072 · **Priorité** P1 · **Taille** S · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-070 · **Labels** python, observabilité

#### Contexte

§12.5 : logs JSON corrélés aux traces ; pas de données brutes de capteurs, de prompts LLM ni de données personnelles par défaut.

#### Tâches proposées

- Format du §12.5 ; filtre d'expurgation configurable.
- Corrélation `trace_id` et `span_id`.

#### Critères d'acceptation

- Test : un prompt LLM n'apparaît jamais dans les logs par défaut.

#### Fichiers concernés

- `src/hypomnesis/observability/logging.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
