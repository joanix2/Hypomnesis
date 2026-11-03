---
title: "HYP-082 · Sorties LLM au grade `Hypothesis` et détection des manques"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 7 — Intégration LLM · dépend de HYP-081, HYP-032"
---

## Conversation

### user

**Ticket** HYP-082 · **Priorité** P1 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-081, HYP-032 · **Labels** python, llm

#### Contexte

§14.4 : les informations manquantes restent explicites ; le LLM ne doit pas inventer les valeurs. Propriété P12 (monotonie du support).

#### Tâches proposées

- Toute valeur littérale introduite par le LLM sans source a le support `Hypothesis`.
- Les valeurs absentes deviennent des métavariables à résoudre par les estimateurs.
- Rapport des informations manquantes à l'utilisateur.

#### Critères d'acceptation

- « Estime son épaisseur » produit une métavariable résolue par l'estimateur, et non une valeur inventée par le LLM.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
