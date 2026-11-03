---
id: HYP-062
title: "Permissions et pipeline de validation des effets"
status: backlog
priority: P0
size: M
epic: P5-EFFETS
depends_on: [HYP-061, HYP-042]
labels: [python]
assignee: 
---

# HYP-062 — Permissions et pipeline de validation des effets

## Contexte

§9.8 : structure JSON, contrat, permissions, contraintes métier, sécurité, puis exécution ; validation humaine possible.

## Tâches

- [ ] `effects/permissions.py` : politiques de permissions déclaratives.
- [ ] `effects/dispatcher.py` : applique les étapes 1 à 9 du §9.8 dans l'ordre, journalise chacune.
- [ ] Point d'extension pour une validation humaine obligatoire.

## Critères d'acceptation

- [ ] Une commande invalide est rejetée avant tout appel d'actionneur (critère §16.4).
- [ ] Une action non autorisée ne peut pas être exécutée (critère §16.4).
- [ ] Le journal permet de reconstruire la trace de chaque commande.

## Fichiers concernés

- `src/hypomnesis/effects/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
