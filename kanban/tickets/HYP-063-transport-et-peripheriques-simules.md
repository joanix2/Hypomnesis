---
id: HYP-063
title: "Transport JSON par fichiers et périphériques simulés"
status: backlog
priority: P0
size: M
epic: P5-EFFETS
depends_on: [HYP-062]
labels: [python]
assignee: 
---

# HYP-063 — Transport JSON par fichiers et périphériques simulés

## Contexte

§9.5 : fichiers JSON pour le MVP, contrat séparé du transport ; capteurs et actionneurs simulés.

## Tâches

- [ ] Interface de transport ; implémentations mémoire et fichiers.
- [ ] Capteur de température simulé, actionneur de ventilateur simulé, avec manifestes et schémas.
- [ ] Enregistrement et rejeu de scénarios.

## Critères d'acceptation

- [ ] Tous les messages passent par l'enveloppe `envelope/1.0.0`.
- [ ] Un scénario enregistré se rejoue à l'identique.

## Fichiers concernés

- `src/hypomnesis/effects/transports/`
- `examples/robotics/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
