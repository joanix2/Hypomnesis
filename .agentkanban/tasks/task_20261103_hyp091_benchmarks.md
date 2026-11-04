---
title: "HYP-091 · Benchmarks de bout en bout"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Phase 8 — Stabilisation · dépend de HYP-090"
priority: P2
tags: [mvp, outillage, performance, tests]
---

## Conversation

### user

**Ticket** HYP-091 · **Priorité** P2 · **Taille** M · **Epic** Phase 8 — Stabilisation · **Dépend de** HYP-090 · **Labels** perf

#### Contexte

§17 phase 8 : ajouter les benchmarks.

#### Tâches proposées

- Benchmarks du scénario MVP et des étapes coûteuses (typage, solveur, estimateur).
- Suivi des régressions en CI.

#### Critères d'acceptation

- Résultats publiés et comparés à la précédente exécution.

#### Fichiers concernés

- `tests/benchmarks/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Baseline du lot Mac, f35b5e0, macOS ARM64/Python 3.12.15 : une chauffe,
cinq répétitions, médiane parsing/typage de certifiable.hyp avec prélude
0,027478 s ; scénario mécanique complet 0,678374 s. Le scénario utilise
RecordedClient et une réponse figée : ce n'est pas une mesure d'inférence.
Sorties de mesure et harnais conservés dans le workspace de session.
Cette capture initiale ne clôt pas HYP-091 : restent les mesures des
étapes coûteuses, le banc versionné et la comparaison publiée en CI.

### user
