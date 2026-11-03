---
title: "HYP-046 · Théories : signatures avec lois, modèles et tests de lois"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Niveau M3 (méta-métamodèle) · dépend de HYP-012"
---

## Conversation

### user

**Ticket** HYP-046 · **Priorité** P1 · **Taille** L · **Epic** Niveau M3 (méta-métamodèle) · **Dépend de** HYP-012 · **Labels** python

#### Contexte

Étape 2 de prototypage de `docs/architecture/m3-metalangage.md` (§8) : une théorie est une signature de module enrichie de `law` ; un plugin en est un modèle (style tagless-final). Les lois sont vérifiées par tests de propriétés sur chaque modèle.

#### Tâches proposées

- Syntaxe `law nom : expr = expr` dans les signatures.
- Générer pour chaque modèle des tests Hypothesis vérifiant chaque loi.
- Exemple : théorie `Dimension` (groupe abélien) et deux modèles.

#### Critères d'acceptation

- Un modèle qui viole une loi est détecté par les tests générés.
- ADR sur la syntaxe des lois.

#### Fichiers concernés

- `src/hypomnesis/language/`
- `examples/`

#### Références

- `docs/architecture/m3-metalangage.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
