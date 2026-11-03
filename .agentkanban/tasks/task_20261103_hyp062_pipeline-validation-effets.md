---
title: "HYP-062 · Permissions et pipeline de validation des effets"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 5 — Effets et actionneurs · dépend de HYP-061, HYP-042"
---

## Conversation

### user

**Ticket** HYP-062 · **Priorité** P0 · **Taille** M · **Epic** Phase 5 — Effets et actionneurs · **Dépend de** HYP-061, HYP-042 · **Labels** python

#### Contexte

§9.8 : structure JSON, contrat, permissions, contraintes métier, sécurité, puis exécution ; validation humaine possible.

#### Tâches proposées

- `effects/permissions.py` : politiques de permissions déclaratives.
- `effects/dispatcher.py` : applique les étapes 1 à 9 du §9.8 dans l'ordre, journalise chacune.
- Point d'extension pour une validation humaine obligatoire.

#### Critères d'acceptation

- Une commande invalide est rejetée avant tout appel d'actionneur (critère §16.4).
- Une action non autorisée ne peut pas être exécutée (critère §16.4).
- Le journal permet de reconstruire la trace de chaque commande.

#### Fichiers concernés

- `src/hypomnesis/effects/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
