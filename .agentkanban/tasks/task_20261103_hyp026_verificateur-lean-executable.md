---
title: "HYP-026 · Pont F3c : exécutable Lean `hypomnesis-check`"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Vérification formelle (Lean) · dépend de HYP-025, HYP-020"
---

## Conversation

### user

**Ticket** HYP-026 · **Priorité** P0 · **Taille** M · **Epic** Vérification formelle (Lean) · **Dépend de** HYP-025, HYP-020 · **Labels** lean

#### Contexte

Le vérificateur `typeOf`, prouvé correct, doit pouvoir lire un certificat JSON produit par Python.

#### Tâches proposées

- Ajouter une cible `lean_exe hypomnesis-check` dans `formal/lakefile.toml`.
- Décoder le JSON (`Lean.Json`) vers `Expr`, `Ty` et Σ ; retourner un code de sortie et un diagnostic en cas de refus.
- Sous-commande `eval` exposant l'interpréteur de référence (utilisée par HYP-028).

#### Critères d'acceptation

- `lake exe hypomnesis-check cert.json` accepte les certificats des exemples et refuse un certificat altéré à la main.
- Le décodeur est séparé du noyau prouvé : seul `typeOf` fait partie de la base de confiance.

#### Fichiers concernés

- `formal/lakefile.toml`
- `formal/Main.lean`
- `formal/Hypomnesis/Certificate.lean`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
