---
title: "HYP-037 · Lean F4b : pas de faux conflit"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Vérification formelle (Lean) · dépend de HYP-035, HYP-036"
priority: P2
tags: [epistemique, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-037 · **Priorité** P2 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-035, HYP-036 · **Labels** lean

#### Contexte

Si le moteur signale `Conflict`, l'incompatibilité est réellement dérivable des faits courants.

#### Tâches proposées

- Modéliser la détection de HYP-035 ; prouver sa correction (et sa complétude si elle est visée).

#### Critères d'acceptation

- Théorème sans `sorry`, ajouté à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte OBJ-11 et la spécification v0.3 §7.1 : `Conflict` appartient
à la cohérence, pas au support. La preuve devra établir une incompatibilité
réelle sans confondre estimation, inconnue et contradiction ; elle demeure
à réaliser dans ce ticket.

### user
