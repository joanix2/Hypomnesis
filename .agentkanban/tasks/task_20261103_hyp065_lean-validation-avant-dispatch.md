---
title: "HYP-065 · Lean F5a : validation et autorisation avant tout dispatch"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Vérification formelle (Lean) · dépend de HYP-062"
---

## Conversation

### user

**Ticket** HYP-065 · **Priorité** P0 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-062 · **Labels** lean

#### Contexte

Propriété de trace la plus importante du projet (§9.8, critères §16.4) : elle porte sur des actions physiques.

#### Tâches proposées

- Modéliser le dispatcher de HYP-062 comme système de transitions produisant une trace d'événements.
- Prouver : dans toute trace, chaque `dispatch c` est précédé de `validated c` puis `authorized c`.
- Prouver : aucun `dispatch c` sans permission accordée pour `c`.

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit et à `proprietes.md`.
- La correspondance modèle ↔ `dispatcher.py` est documentée ligne à ligne.

#### Fichiers concernés

- `formal/Hypomnesis/Effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
