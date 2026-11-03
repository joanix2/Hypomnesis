---
id: HYP-066
title: "Lean F5b : au plus une exécution des commandes non idempotentes"
status: backlog
priority: P0
size: L
epic: FORMEL
depends_on: [HYP-061]
labels: [lean]
assignee: 
---

# HYP-066 — Lean F5b : au plus une exécution des commandes non idempotentes

## Contexte

§9.7 et risque « Doubles commandes » (§19).

## Tâches

- [ ] Modéliser automate, journal, relances, pertes et duplications de messages.
- [ ] Prouver : une commande non idempotente est exécutée au plus une fois, quelles que soient les pannes modélisées.
- [ ] Prouver : les états terminaux sont absorbants.

## Critères d'acceptation

- [ ] Théorèmes sans `sorry`, ajoutés à l'audit.

## Fichiers concernés

- `formal/Hypomnesis/Effects/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
