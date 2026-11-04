---
title: "HYP-084 · Explicabilité : reformuler ce qui a été compris et fait"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Phase 7 — Intégration LLM · dépend de HYP-081, HYP-031"
priority: P2
tags: [documentation, epistemique, llm, python]
---

## Conversation

### user

**Ticket** HYP-084 · **Priorité** P2 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-081, HYP-031 · **Labels** python, llm

#### Contexte

§14.5 : reformuler ce qui a été compris, les informations utilisées, les hypothèses, règles, validations et actions à venir.

#### Tâches proposées

- Construire l'explication à partir de la provenance (termes et journal), et non d'une génération libre.
- Le LLM peut mettre en forme, mais chaque affirmation renvoie à une entrée de provenance.

#### Critères d'acceptation

- Chaque phrase de l'explication cite un identifiant de fait, de règle ou de commande.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
