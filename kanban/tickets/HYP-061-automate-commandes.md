---
id: HYP-061
title: "Automate d'états des commandes, délais, relances"
status: backlog
priority: P0
size: M
epic: P5-EFFETS
depends_on: [HYP-060]
labels: [python]
assignee: 
---

# HYP-061 — Automate d'états des commandes, délais, relances

## Contexte

§9.7 : `Created` → `Validated` → `Authorized` → `Dispatched` → `Accepted` → `Completed`, plus les états d'échec ; idempotence.

## Tâches

- [ ] Automate explicite (table des transitions), états terminaux absorbants.
- [ ] Identifiants de commande, délais d'expiration, politique de relance.
- [ ] Déduplication par `command_id` : une commande non idempotente n'est jamais relancée automatiquement.

## Critères d'acceptation

- [ ] Test exhaustif des transitions autorisées et interdites.
- [ ] Simulation de pannes de transport : aucune double exécution d'une commande non idempotente.

## Fichiers concernés

- `src/hypomnesis/effects/commands.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
