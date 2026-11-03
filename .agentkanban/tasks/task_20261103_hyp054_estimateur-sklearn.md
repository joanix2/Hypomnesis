---
title: "HYP-054 · Estimateur scikit-learn (épaisseur de plaque)"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P0 · M · Phase 4 — Raisonnement hybride · dépend de HYP-044, HYP-032"
---

## Conversation

### user

**Ticket** HYP-054 · **Priorité** P0 · **Taille** M · **Epic** Phase 4 — Raisonnement hybride · **Dépend de** HYP-044, HYP-032 · **Labels** python

#### Contexte

Estimateur initial (§15.1) ; il propose une valeur pour la métavariable « épaisseur » du scénario MVP.

#### Tâches proposées

- Petit modèle entraîné sur un jeu synthétique documenté, versionné.
- Résultat de support `Estimated`, avec modèle, version et incertitude dans la provenance (§7.2).

#### Critères d'acceptation

- La provenance de l'épaisseur estimée contient le modèle et sa version.

#### Fichiers concernés

- `src/hypomnesis/backends/sklearn/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
