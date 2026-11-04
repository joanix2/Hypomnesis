---
title: "HYP-056 · Types dimensionnels (unification modulo groupe abélien)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · L · Phase 4 — Raisonnement hybride · dépend de HYP-002"
priority: P2
tags: [compilateur, dsl, metalangage, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-056 · **Priorité** P2 · **Taille** L · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§5.3 et §6.5 de `docs/architecture/m3-metalangage.md`. Les dimensions forment un groupe abélien libre ; l'unification modulo AG est décidable (Kennedy, ESOP 1994). Le noyau ne doit connaître aucune unité : la théorie est déclarée par une bibliothèque.

#### Tâches proposées

- Types indexés par dimension (`float<m/s>`), inférence avec unification AG.
- Bibliothèque `Units` déclarant dimensions de base et conversions.
- Réécrire `examples/mechanics/units.hyp` avec ces types.

#### Critères d'acceptation

- `m + s` refusé ; `m / s * s` accepté comme `m` ; types principaux inférés.
- ADR rédigée.

#### Fichiers concernés

- `src/hypomnesis/language/typesystem/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
