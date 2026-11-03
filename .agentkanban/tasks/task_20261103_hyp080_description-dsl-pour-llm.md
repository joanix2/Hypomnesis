---
title: "HYP-080 · Publication des DSL pour les LLM"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 7 — Intégration LLM · dépend de HYP-041"
---

## Conversation

### user

**Ticket** HYP-080 · **Priorité** P1 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-041 · **Labels** python, llm

#### Contexte

§14.2 : la génération s'appuie sur les descriptions de domaines, signatures, grammaires, catalogues de plugins et permissions.

#### Tâches proposées

- Commande `hypomnesis describe` : export structuré (JSON et Markdown) des modules, types, signatures et plugins accessibles.
- Taille maîtrisée : sélection par domaine.

#### Critères d'acceptation

- La description du domaine `Mechanics` tient dans un prompt et liste toutes les valeurs publiques avec leurs types.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
