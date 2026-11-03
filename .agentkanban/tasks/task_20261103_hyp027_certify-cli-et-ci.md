---
title: "HYP-027 · Pont F3d : `hypomnesis check --certify` et certification en CI"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · S · Vérification formelle (Lean) · dépend de HYP-026, HYP-004"
---

## Conversation

### user

**Ticket** HYP-027 · **Priorité** P0 · **Taille** S · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-026, HYP-004 · **Labels** python, ci

#### Contexte

Dernière étape du pont : rendre la certification utilisable et systématique.

#### Tâches proposées

- `--certify` : émettre le certificat, appeler `hypomnesis-check`, échouer si refusé.
- Job CI qui certifie tous les fichiers de `examples/`.
- Mettre à jour la ligne P3 de `proprietes.md` (garantie de bout en bout).

#### Critères d'acceptation

- CI verte avec certification ; un exemple volontairement mal élaboré, injecté dans un test, est refusé.

#### Fichiers concernés

- `src/hypomnesis/cli.py`
- `.github/workflows/ci.yml`
- `docs/verification/proprietes.md`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
