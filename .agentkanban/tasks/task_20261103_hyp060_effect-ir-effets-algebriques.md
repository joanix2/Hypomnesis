---
title: "HYP-060 · Effect IR et effets algébriques"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · L · Phase 5 — Effets et actionneurs · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-060 · **Priorité** P0 · **Taille** L · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§10 et §6.3 de `docs/architecture/m3-metalangage.md` : un effet est une signature d'opérations ; un programme à effets est une valeur (un terme libre) ; seul le runtime l'interprète, via un handler. Le noyau reste pur (ADR 0003).

#### Tâches proposées

- Syntaxe des signatures d'effets et du type des calculs (`'a effect`), avec `return` et `bind` (§10.2).
- `ir/effect.py` : lecture de source, invocation de plugin, construction de commande, attente, vérification.
- Garantir statiquement qu'aucun terme pur n'exécute d'effet.

#### Critères d'acceptation

- Un programme qui décrit un mouvement de moteur s'évalue en une valeur inerte tant qu'aucun handler ne l'exécute.
- ADR sur la représentation des effets.

#### Fichiers concernés

- `src/hypomnesis/ir/effect.py`
- `src/hypomnesis/effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
