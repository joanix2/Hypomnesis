---
title: "HYP-036 · Lean F4a : révision incrémentale = recalcul complet"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Vérification formelle (Lean) · dépend de HYP-033, HYP-003"
priority: P1
tags: [epistemique, lean, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-036 · **Priorité** P1 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-033, HYP-003 · **Labels** lean

#### Contexte

Prouver sur un modèle du moteur que l'algorithme de HYP-033 est exact, et que le journal n'est jamais détruit.

#### Tâches proposées

- Modéliser l'état (faits, provenances, index inverse) et l'opération de révision incrémentale.
- Prouver : `revise_incr s x = recompute (retract s x)`.
- Prouver : le journal après révision étend le journal précédent (préfixe).

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit et à `proprietes.md` (lot F4).

#### Fichiers concernés

- `formal/Hypomnesis/Epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte OBJ-11 et les axes épistémiques en spécification v0.3.
Le modèle de révision devra respecter cette séparation et le journal en ajout
seul. La correction incrémentale reste une obligation de ce ticket, non une
preuve acquise par l'adoption de la spécification.

### user
