---
title: "HYP-040 · Interfaces des capacités (Observer … Resolver)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 3 — Extensions et contrats · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-040 · **Priorité** P0 · **Taille** M · **Epic** Phase 3 — Extensions et contrats · **Dépend de** HYP-002 · **Labels** python

#### Contexte

§6 : neuf interfaces génériques. Leur rôle type-théorique est décrit au §4.4 de `docs/architecture/m3-metalangage.md` (estimateur = proposer une métavariable, validateur = rendre un certificat, etc.).

#### Tâches proposées

- `src/hypomnesis/capabilities/` : un protocole typé par interface, indépendant du backend.
- Chaque appel rend un résultat structuré (valeur, certificat, diagnostic), jamais une exception brute.
- Docstrings reliant chaque interface au §6 et au §4.4 de la note M3.

#### Critères d'acceptation

- Pyright strict sur le module ; un plugin factice de chaque type passe les tests de conformité.

#### Fichiers concernés

- `src/hypomnesis/capabilities/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
