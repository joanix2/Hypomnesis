---
title: "HYP-070 · Instrumentation OpenTelemetry (traces)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 6 — Observabilité · dépend de HYP-044"
---

## Conversation

### user

**Ticket** HYP-070 · **Priorité** P1 · **Taille** M · **Epic** Phase 6 — Observabilité · **Dépend de** HYP-044 · **Labels** python, observabilité

#### Contexte

§12.3 : un identifiant d'exécution et les spans `hypomnesis.run`, `language.parse`, `language.typecheck`, `observer.read`, … ; ADR 0005.

#### Tâches proposées

- `observability/tracing.py` ; spans aux étapes listées au §12.3, avec les attributs recommandés.
- Propagation du `trace_context` dans l'enveloppe de message.
- Désactivable sans changer aucun résultat.

#### Critères d'acceptation

- Une exécution du scénario produit l'arbre de spans du §12.3.
- Résultats identiques avec ou sans télémétrie (test).

#### Fichiers concernés

- `src/hypomnesis/observability/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
