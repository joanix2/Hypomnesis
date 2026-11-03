---
id: HYP-055
title: "Validateurs et contre-exemples"
status: backlog
priority: P1
size: M
epic: P4-RAISONNEMENT
depends_on: [HYP-052]
labels: [python]
assignee: 
---

# HYP-055 — Validateurs et contre-exemples

## Contexte

§11.6 : vérification des résultats et production éventuelle de contre-exemples.

## Tâches

- [ ] Interface `Validator` concrète : rend une preuve d'acceptation ou un contre-exemple vérifiable.
- [ ] Validateur géométrique pour la plaque.

## Critères d'acceptation

- [ ] Un rejet est toujours accompagné d'un contre-exemple que l'on peut revérifier indépendamment.

## Fichiers concernés

- `src/hypomnesis/engine/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
