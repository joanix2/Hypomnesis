---
id: HYP-068
title: "Scénario MVP secondaire : température → ventilateur"
status: backlog
priority: P0
size: M
epic: P5-EFFETS
depends_on: [HYP-063, HYP-050]
labels: [python, exemple]
assignee: 
---

# HYP-068 — Scénario MVP secondaire : température → ventilateur

## Contexte

§16.3 : un capteur simulé donne une température, une règle produit une commande de ventilateur, un second capteur confirme ou réfute l'effet.

## Tâches

- [ ] Programme d'exemple ; règle métier ; boucle de rétroaction bornée (§11.9).
- [ ] Cas d'échec : l'effet attendu n'est pas observé, l'hypothèse est réfutée et révisée.

## Critères d'acceptation

- [ ] Test d'intégration couvrant succès et réfutation.
- [ ] La frontière noyau pur / effets est visible dans la trace.

## Fichiers concernés

- `examples/robotics/`
- `tests/integration/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
