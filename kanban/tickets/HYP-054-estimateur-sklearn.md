---
id: HYP-054
title: "Estimateur scikit-learn (épaisseur de plaque)"
status: backlog
priority: P0
size: M
epic: P4-RAISONNEMENT
depends_on: [HYP-044, HYP-032]
labels: [python]
assignee: 
---

# HYP-054 — Estimateur scikit-learn (épaisseur de plaque)

## Contexte

Estimateur initial (§15.1) ; il propose une valeur pour la métavariable « épaisseur » du scénario MVP.

## Tâches

- [ ] Petit modèle entraîné sur un jeu synthétique documenté, versionné.
- [ ] Résultat de support `Estimated`, avec modèle, version et incertitude dans la provenance (§7.2).

## Critères d'acceptation

- [ ] La provenance de l'épaisseur estimée contient le modèle et sa version.

## Fichiers concernés

- `src/hypomnesis/backends/sklearn/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
