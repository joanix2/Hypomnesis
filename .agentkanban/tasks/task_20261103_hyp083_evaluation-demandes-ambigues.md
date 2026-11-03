---
title: "HYP-083 · Jeu d'évaluation de demandes ambiguës"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Phase 7 — Intégration LLM · dépend de HYP-081"
---

## Conversation

### user

**Ticket** HYP-083 · **Priorité** P2 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-081 · **Labels** llm, tests

#### Contexte

§17 phase 7 : tester les demandes ambiguës. Évaluation empirique, hors du champ formel (⛔ dans `proprietes.md`).

#### Tâches proposées

- Corpus de demandes avec résultats attendus (programme, ou demande de précision).
- Métriques : taux de programmes bien typés, taux de clarifications pertinentes.

#### Critères d'acceptation

- Rapport reproductible versionné.

#### Fichiers concernés

- `tests/llm_eval/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
