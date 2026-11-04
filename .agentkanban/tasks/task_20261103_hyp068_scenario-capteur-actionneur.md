---
title: "HYP-068 · Scénario MVP secondaire : température → ventilateur"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-063, HYP-050"
priority: P0
tags: [dsl, effets, exemple, moteur-symbolique, mvp, python]
---

## Conversation

### user

**Ticket** HYP-068 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-063, HYP-050 · **Labels** python, exemple

#### Contexte

§16.3 : un capteur simulé donne une température, une règle produit une commande de ventilateur, un second capteur confirme ou réfute l'effet.

#### Tâches proposées

- Programme d'exemple ; règle métier ; boucle de rétroaction bornée (§11.9).
- Cas d'échec : l'effet attendu n'est pas observé, l'hypothèse est réfutée et révisée.

#### Critères d'acceptation

- Test d'intégration couvrant succès et réfutation.
- La frontière noyau pur / effets est visible dans la trace.

#### Fichiers concernés

- `examples/robotics/`
- `tests/integration/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
