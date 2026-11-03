---
title: "HYP-041 · Registre de capacités et manifestes"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 3 — Extensions et contrats · dépend de HYP-040"
---

## Conversation

### user

**Ticket** HYP-041 · **Priorité** P0 · **Taille** M · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-040 · **Labels** python, contrats

#### Contexte

§6.1 : une extension doit être découvrable et inspectable sans exécuter son code métier. Le schéma `extension-manifest/1.0.0` existe déjà dans `src/hypomnesis/contracts/schemas/`.

#### Tâches proposées

- `engine/registry.py` : charger des manifestes JSON, les valider, indexer par identifiant, rôle et version.
- Résolution de dépendances entre extensions avec contraintes de version.
- `hypomnesis plugins list|show` dans la CLI.

#### Critères d'acceptation

- Un manifeste invalide est refusé à l'enregistrement.
- L'inspection ne charge pas le code Python de l'extension (vérifié par test).

#### Fichiers concernés

- `src/hypomnesis/engine/registry.py`
- `src/hypomnesis/cli.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
