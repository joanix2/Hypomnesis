---
id: HYP-050
title: "Moteur de règles avec provenance"
status: backlog
priority: P0
size: L
epic: P4-RAISONNEMENT
depends_on: [HYP-031, HYP-038]
labels: [python]
assignee: 
---

# HYP-050 — Moteur de règles avec provenance

## Contexte

§5.4 et §8 : règles de déduction, par défaut, conditionnelles ; chaque conclusion porte sa provenance.

## Tâches

- [ ] Syntaxe ou bibliothèque de règles ; chaînage avant jusqu'à point fixe, avec budget.
- [ ] Règles par défaut : conclusions de support `Defaulted`, retirées si une observation les contredit.
- [ ] Intégration avec la révision (HYP-033).

## Critères d'acceptation

- [ ] Une conclusion dérivée d'une observation et d'une estimation a le support `Estimated`.
- [ ] Le chaînage termine sous budget et le signale si le budget est atteint.

## Fichiers concernés

- `src/hypomnesis/engine/rules.py`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
