---
title: "HYP-013 · Benchmarks et performance de l'interpréteur"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P3 · M · Langage · dépend de HYP-002"
priority: P3
tags: [outillage, performance, python, runtime, tests]
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

### agent

Baseline CPU avant toute modification du runtime, lot Mac approuvé :
révision f35b5e0, macOS ARM64, Python 3.12.15, une chauffe puis cinq mesures
(médianes, aucune inférence LLM).

- Boucle terminale 1 000 000 : 1,311431 s.
- Tri de 500 entiers décroissants par List.sort compare : 0,033138 s.
- Arbre récursif profondeur 11 : 0,004514 s.
- Prélude map carrés puis fold sur 500 éléments : 0,002872 s.

Cette capture ne satisfait pas HYP-013 : ni optimisation ni gain 2× mesuré.
Harnais et échantillons conservés dans le workspace de session ; ils seront
repris dans le banc versionné au moment de ce ticket, avant l'optimisation.

### user
