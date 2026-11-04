---
title: "HYP-038 · Exposer les connaissances dans le langage"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-030, HYP-033"
priority: P1
tags: [dsl, epistemique, metalangage, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-038 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-030, HYP-033 · **Labels** python

#### Contexte

Les programmes Hypomnesis doivent pouvoir manipuler les connaissances (§2 OBJ-04, §5) sans effet de bord : lecture d'une base immuable passée en argument, construction de faits dérivés.

#### Tâches proposées

- Bibliothèque `Knowledge` (types et fonctions natives pures) : interroger, dériver, consulter la provenance et le support.
- Les primitives passent par le registre natif fermé (ADR 0003).
- Exemple `examples/knowledge/` sur la plaque.

#### Critères d'acceptation

- Un programme dérive un fait dont le support est calculé automatiquement (Estimated si une prémisse l'est).

#### Fichiers concernés

- `src/hypomnesis/stdlib/`
- `src/hypomnesis/runtime/natives.py`
- `examples/knowledge/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

Référence adoptée par HYP-005 : spécification v0.3 §7.1. Exposer les axes
indépendamment ; `Derived` est une justification, son support vient des
prémisses. L'exemple d'une prémisse estimée reste valable sans supposer
l'absence de prémisses moins étayées. Conserver les primitives pures et le
registre fermé ; les démonstrations suivent désormais `demo/` (ADR 0011).

### user
