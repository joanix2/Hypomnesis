---
title: "HYP-015 · Traces : remplacer le traceur maison par le SDK OpenTelemetry"
lane: todo
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P1 · M · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-015 · **Priorité** P1 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, observabilité, dette

#### Contexte

`src/hypomnesis/observability/trace.py` reproduit à la main une petite partie d'OpenTelemetry (spans imbriqués, attributs, statut). Le SDK officiel fournit la même chose, plus la propagation du contexte et l'export OTLP. Ce ticket remplace le traceur ; HYP-070 complète ensuite l'instrumentation et l'export vers un collecteur.

#### Tâches proposées

- Utiliser `opentelemetry-sdk` avec un exportateur en mémoire pour construire l'arbre de spans et l'export JSON des rapports M0.
- Conserver les noms de spans du §12.3 et les attributs actuels.
- Relier le `trace_id` OpenTelemetry au `trace_context` de l'enveloppe de message (§9.6).
- Garantir que désactiver la télémétrie ne change aucun résultat (ADR 0005).

#### Critères d'acceptation

- Les rapports M0 contiennent toujours l'arbre de spans, désormais produit par OpenTelemetry.
- Un test vérifie qu'un run avec et sans télémétrie donne les mêmes connaissances.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/observability/trace.py`
- `src/hypomnesis/engine/procedure.py`
- `pyproject.toml`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)
