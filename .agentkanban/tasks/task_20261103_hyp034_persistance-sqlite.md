---
title: "HYP-034 · Persistance SQLite et import/export JSON"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-033"
---

## Conversation

### user

**Ticket** HYP-034 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-033 · **Labels** python

#### Contexte

§7.4 : structures immuables en mémoire, journal d'événements, SQLite pour la persistance, JSON pour les échanges.

#### Tâches proposées

- Schéma SQLite du journal ; reconstruction de l'état par rejeu.
- Export et import JSON validés par schéma.
- Migrations versionnées.

#### Critères d'acceptation

- Rejouer le journal persistant redonne exactement l'état en mémoire.
- Import d'un fichier invalide refusé avec le chemin de l'erreur.

#### Fichiers concernés

- `src/hypomnesis/epistemics/storage.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
