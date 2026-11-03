---
title: "HYP-092 · Documentation de création de domaine et SDK expérimental"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Phase 8 — Stabilisation · dépend de HYP-090, HYP-046"
---

## Conversation

### user

**Ticket** HYP-092 · **Priorité** P2 · **Taille** M · **Epic** Phase 8 — Stabilisation · **Dépend de** HYP-090, HYP-046 · **Labels** doc

#### Contexte

§17 phase 8 : documenter la création de domaines, publier un SDK expérimental ; hypothèse H1.

#### Tâches proposées

- Guide pas à pas : créer un domaine (théorie, modèles, plugins, contrats) sans modifier le noyau.
- Deuxième domaine indépendant (logistique ou finance) écrit en suivant le guide.

#### Critères d'acceptation

- Le second domaine est créé sans aucune modification de `src/hypomnesis/` (vérifié par le diff).

#### Fichiers concernés

- `docs/`
- `examples/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
