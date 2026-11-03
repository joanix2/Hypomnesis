---
title: "HYP-013 · Benchmarks et performance de l'interpréteur"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P3 · M · Langage · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-013 · **Priorité** P3 · **Taille** M · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python, perf

#### Contexte

Une boucle d'un million d'itérations prend quelques secondes. Les variables locales sont résolues par nom en remontant une chaîne d'environnements.

#### Tâches proposées

- Créer `tests/benchmarks/` (pytest-benchmark ou script) : boucle, tri de liste, arbre binaire, prélude.
- Résoudre les variables locales en indices (profondeur, position) à la compilation.
- Mesurer avant et après, et consigner les chiffres dans le ticket.

#### Critères d'acceptation

- Gain mesuré d'au moins 2× sur la boucle, sans régression des tests.
- Les tests différentiels (HYP-028), s'ils existent déjà, passent.

#### Fichiers concernés

- `src/hypomnesis/runtime/interpreter.py`
- `tests/benchmarks/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
