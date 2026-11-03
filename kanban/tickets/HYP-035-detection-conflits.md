---
id: HYP-035
title: "Détection et signalement des conflits"
status: backlog
priority: P1
size: M
epic: P2-EPISTEMIQUE
depends_on: [HYP-033]
labels: [python]
assignee: 
---

# HYP-035 — Détection et signalement des conflits

## Contexte

Statut `Conflict` (§7.1) : informations incompatibles ; contradictions signalées lors de la révision (§7.3 étape 5).

## Tâches

- [ ] Définir l'incompatibilité : deux valeurs distinctes pour un attribut fonctionnel, violation d'un invariant déclaré.
- [ ] Rapport de conflit : faits en cause et leurs provenances.
- [ ] Politiques de résolution configurables (préférer le meilleur support, signaler sans trancher).

## Critères d'acceptation

- [ ] Aucun conflit signalé sans incompatibilité réelle (test par construction).
- [ ] Le rapport cite les observations à l'origine du conflit.

## Fichiers concernés

- `src/hypomnesis/epistemics/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
