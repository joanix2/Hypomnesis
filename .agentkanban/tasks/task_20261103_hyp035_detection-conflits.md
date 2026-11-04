---
title: "HYP-035 · Détection et signalement des conflits"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Phase 2 — Moteur épistémique · dépend de HYP-033"
priority: P1
tags: [epistemique, moteur-symbolique, python]
---

## Conversation

### user

**Ticket** HYP-035 · **Priorité** P1 · **Taille** M · **Epic** Phase 2 — Moteur épistémique · **Dépend de** HYP-033 · **Labels** python

#### Contexte

Statut `Conflict` (§7.1) : informations incompatibles ; contradictions signalées lors de la révision (§7.3 étape 5).

#### Tâches proposées

- Définir l'incompatibilité : deux valeurs distinctes pour un attribut fonctionnel, violation d'un invariant déclaré.
- Rapport de conflit : faits en cause et leurs provenances.
- Politiques de résolution configurables (préférer le meilleur support, signaler sans trancher).

#### Critères d'acceptation

- Aucun conflit signalé sans incompatibilité réelle (test par construction).
- Le rapport cite les observations à l'origine du conflit.

#### Fichiers concernés

- `src/hypomnesis/epistemics/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

HYP-005 adopte les axes du §7.1 de la spécification v0.3. `Conflict` relève
de la cohérence, indépendamment du support. Une préférence pour le meilleur
support ne doit pas masquer les incompatibilités ni effacer leurs provenances.
Les critères historiques de détection restent applicables.

### user
