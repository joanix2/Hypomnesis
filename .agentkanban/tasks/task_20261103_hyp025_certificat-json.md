---
title: "HYP-025 · Pont F3b : schéma et export JSON du certificat"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Vérification formelle (Lean) · dépend de HYP-024"
---

## Conversation

### user

**Ticket** HYP-025 · **Priorité** P0 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-024 · **Labels** python, contrats

#### Contexte

Le certificat est la Core IR élaborée, en indices de de Bruijn, sérialisée en JSON et validée par un JSON Schema versionné (ADR 0004).

#### Tâches proposées

- Écrire `src/hypomnesis/contracts/schemas/certificate-1.0.0.json` (Draft 2020-12).
- Écrire `src/hypomnesis/certify/export.py` : traduction noms → indices, déclarations de types, définitions globales.
- Ajouter `hypomnesis check --emit-certificate FICHIER`.

#### Critères d'acceptation

- Chaque exemple produit un certificat valide contre le schéma.
- Test d'aller-retour : réimporter le certificat redonne une Core IR équivalente.

#### Fichiers concernés

- `src/hypomnesis/contracts/schemas/`
- `src/hypomnesis/certify/`
- `src/hypomnesis/cli.py`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
