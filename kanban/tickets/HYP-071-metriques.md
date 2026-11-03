---
id: HYP-071
title: "Métriques du §12.4"
status: backlog
priority: P1
size: M
epic: P6-OBSERVABILITE
depends_on: [HYP-070]
labels: [python, observabilité]
assignee: 
---

# HYP-071 — Métriques du §12.4

## Contexte

Tableau des métriques du §12.4 ; labels sans identifiants à forte cardinalité.

## Tâches

- [ ] Compteurs et histogrammes listés ; export OTLP.
- [ ] Test qui refuse un label de métrique contenant un identifiant de message, de trace ou de connaissance.

## Critères d'acceptation

- [ ] Toutes les métriques du §12.4 sont émises par le scénario MVP.

## Fichiers concernés

- `src/hypomnesis/observability/metrics.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
