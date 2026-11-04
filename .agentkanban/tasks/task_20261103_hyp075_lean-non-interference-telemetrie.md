---
title: "HYP-075 · Lean : la télémétrie n'influe pas sur les résultats"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P3 · M · Vérification formelle (Lean) · dépend de HYP-070, HYP-036"
priority: P3
tags: [effets, lean, moteur-symbolique, observabilite]
---

## Conversation

### user

**Ticket** HYP-075 · **Priorité** P3 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-070, HYP-036 · **Labels** lean

#### Contexte

ADR 0005 et §12.8 : la provenance et l'observabilité restent distinctes.

#### Tâches proposées

- Modéliser l'exécution instrumentée comme une exécution enrichie d'émissions de télémétrie.
- Prouver que la projection sur les résultats est identique à l'exécution non instrumentée.

#### Critères d'acceptation

- Théorème sans `sorry`, ajouté à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
