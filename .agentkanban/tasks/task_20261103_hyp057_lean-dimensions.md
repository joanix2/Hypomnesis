---
title: "HYP-057 · Lean F6 : cohérence dimensionnelle et invariance d'échelle"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · L · Vérification formelle (Lean) · dépend de HYP-056, HYP-023"
priority: P2
tags: [lean, metalangage, moteur-symbolique]
---

## Conversation

### user

**Ticket** HYP-057 · **Priorité** P2 · **Taille** L · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-056, HYP-023 · **Labels** lean

#### Contexte

Paramétricité des unités (Kennedy, POPL 1997) : une fonction polymorphe en dimension commute avec le changement d'échelle.

#### Tâches proposées

- Formaliser les types dimensionnels du fragment.
- Prouver la sûreté et le théorème d'invariance par changement d'unités (relation logique).

#### Critères d'acceptation

- Théorèmes sans `sorry`, ajoutés à l'audit.

#### Fichiers concernés

- `formal/Hypomnesis/Dimensions/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
