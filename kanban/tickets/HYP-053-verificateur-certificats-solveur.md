---
id: HYP-053
title: "Vérificateur de certificats de solveur (+ preuve Lean)"
status: backlog
priority: P1
size: M
epic: P4-RAISONNEMENT
depends_on: [HYP-052]
labels: [python, lean]
assignee: 
---

# HYP-053 — Vérificateur de certificats de solveur (+ preuve Lean)

## Contexte

§4.5 de `docs/architecture/m3-metalangage.md` : seul le noyau rend un fait `Derived`. Un modèle Z3 est accepté après vérification qu'il satisfait toutes les contraintes, par évaluation indépendante de Z3.

## Tâches

- [ ] Évaluateur de contraintes de la Problem IR sur une affectation.
- [ ] Lean : modéliser cet évaluateur et prouver qu'un modèle accepté satisfait les contraintes.

## Critères d'acceptation

- [ ] Un modèle volontairement faux est refusé.
- [ ] Théorème Lean ajouté à l'audit.

## Fichiers concernés

- `src/hypomnesis/engine/`
- `formal/Hypomnesis/Problem/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
