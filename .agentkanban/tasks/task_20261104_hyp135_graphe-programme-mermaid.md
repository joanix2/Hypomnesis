---
title: "HYP-135 · Graphe d'un programme et compilation vers Mermaid"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P2 · M · Outillage et visualisation · dépend de HYP-002"
priority: P2
tags: [dsl, metalangage, outillage, python, transpileurs, visualisation]
---

## Conversation

### user

**Ticket** HYP-135 · **Priorité** P2 · **Taille** M · **Epic** Outillage et visualisation · **Dépend de** HYP-002 · **Labels** python, visualisation

#### Contexte

Première visualisation des programmes et des langages. Mermaid n'est qu'une sortie : un modèle de graphe intermédiaire évite de tout réécrire pour React Flow (HYP-136). Le code reste générique : aucun concept de domaine dans le moteur (ADR 0008).

#### Tâches proposées

- Modèle de graphe indépendant du rendu (nœuds, arêtes, types, position dans le source), construit avec NetworkX et publié en JSON avec son schéma.
- Vue statique, depuis la Core IR : dépendances entre définitions et modules.
- Vue du pipeline, depuis la trace d'une exécution en `simulate` ou `dry-run` : une procédure pouvant être d'ordre supérieur, ses étapes ne se déduisent pas toujours du texte du programme.
- Commande `hypomnesis graph --format mermaid|json`.

#### Critères d'acceptation

- Les langages mécanique et ventilation produisent chacun un diagramme Mermaid valide, vérifié par un vrai analyseur Mermaid en test.
- La vue du pipeline du scénario de la plaque montre les étapes dans l'ordre de l'exécution.
- Le test d'architecture passe toujours.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/visualization/`
- `src/hypomnesis/cli.py`
- `pyproject.toml`

#### Références

- Lié à HYP-008 (graphe de provenance des faits)
- Conventions et définition de fini : `.agentkanban/memory.md`
