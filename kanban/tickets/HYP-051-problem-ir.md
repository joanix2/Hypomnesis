---
id: HYP-051
title: "Problem IR : variables, domaines, contraintes, objectifs"
status: backlog
priority: P0
size: M
epic: P4-RAISONNEMENT
depends_on: [HYP-002]
labels: [python]
assignee: 
---

# HYP-051 — Problem IR : variables, domaines, contraintes, objectifs

## Contexte

§13.3 : Problem IR (variables, domaines, contraintes, objectifs, états, actions, transitions).

## Tâches

- [ ] `ir/problem.py` : structures immuables ; construction depuis le langage.
- [ ] Sérialisation JSON avec schéma versionné.

## Critères d'acceptation

- [ ] La contrainte du scénario MVP (épaisseur dans une plage, rigidité) s'exprime en Problem IR.

## Fichiers concernés

- `src/hypomnesis/ir/problem.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
