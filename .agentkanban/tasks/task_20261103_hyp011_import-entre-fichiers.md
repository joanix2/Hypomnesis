---
title: "HYP-011 · Import entre fichiers"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P2 · M · Langage · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-011 · **Priorité** P2 · **Taille** M · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python

#### Contexte

La CLI charge les fichiers dans l'ordre donné ; il n'existe pas de dépendance déclarée entre fichiers (§4.1 « Modules et imports »). `examples/mechanics/plate.hyp` dépend implicitement de `units.hyp`.

#### Tâches proposées

- Concevoir la syntaxe (ADR) : par exemple, un fichier `units.hyp` définit le module `Units` et `open Units` le charge à la demande.
- Résoudre les chemins relativement au fichier et à un chemin de recherche ; détecter les cycles.
- Charger chaque fichier une seule fois par session.

#### Critères d'acceptation

- `hypomnesis run examples/mechanics/plate.hyp` fonctionne seul.
- Un import circulaire donne une erreur claire.
- ADR rédigée.

#### Fichiers concernés

- `src/hypomnesis/session.py`
- `src/hypomnesis/cli.py`
- `examples/mechanics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
