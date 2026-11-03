---
title: "HYP-010 · Vérifier l'exhaustivité et la redondance du filtrage"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · M · Langage · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-010 · **Priorité** P1 · **Taille** M · **Epic** Langage · **Dépend de** HYP-002 · **Labels** python

#### Contexte

Aujourd'hui un `match` non exhaustif n'est détecté qu'à l'exécution (`Match_failure`). Le vérificateur connaît tous les constructeurs de chaque type et peut décider l'exhaustivité (algorithme de Maranget, « Warnings for pattern matching », JFP 2007).

#### Tâches proposées

- Implémenter l'analyse sur les motifs de la Core IR (constructeurs, tuples, records, littéraux, alternatives).
- Émettre un avertissement positionné avec un exemple de valeur non couverte ; signaler les bras inaccessibles.
- Ajouter une option `--strict` à la CLI qui transforme les avertissements en erreurs.
- Introduire un canal d'avertissements dans `CheckResult` (il n'existe pas encore).

#### Critères d'acceptation

- `match x with Some y -> y` produit un avertissement citant `None`.
- Aucun avertissement sur le prélude ni sur les exemples.
- Tests unitaires couvrant variants imbriqués, listes, littéraux et gardes (une garde rend le bras non couvrant).

#### Fichiers concernés

- `src/hypomnesis/language/typesystem/`
- `src/hypomnesis/cli.py`
- `tests/unit/`

#### Références

- `docs/language/reference.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
