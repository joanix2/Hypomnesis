---
id: HYP-013
title: "Benchmarks et performance de l'interpréteur"
status: backlog
priority: P3
size: M
epic: LANG
depends_on: [HYP-002]
labels: [python, perf]
assignee: 
---

# HYP-013 — Benchmarks et performance de l'interpréteur

## Contexte

Une boucle d'un million d'itérations prend quelques secondes. Les variables locales sont résolues par nom en remontant une chaîne d'environnements.

## Tâches

- [ ] Créer `tests/benchmarks/` (pytest-benchmark ou script) : boucle, tri de liste, arbre binaire, prélude.
- [ ] Résoudre les variables locales en indices (profondeur, position) à la compilation.
- [ ] Mesurer avant et après, et consigner les chiffres dans le ticket.

## Critères d'acceptation

- [ ] Gain mesuré d'au moins 2× sur la boucle, sans régression des tests.
- [ ] Les tests différentiels (HYP-028), s'ils existent déjà, passent.

## Fichiers concernés

- `src/hypomnesis/runtime/interpreter.py`
- `tests/benchmarks/`

## Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `kanban/README.md`
