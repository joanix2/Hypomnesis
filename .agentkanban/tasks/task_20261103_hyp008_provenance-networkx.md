---
title: "HYP-008 · Graphe de provenance des faits avec NetworkX"
lane: doing
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-04T14:15:00+01:00
description: "P1 · M · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-008 · **Priorité** P1 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, networkx, dette

#### Contexte

`KnowledgeBase` (`src/hypomnesis/epistemics/knowledge.py`) gère à la main les prémisses des faits, l'invalidation en cascade lors d'un retrait et l'explication récursive. NetworkX fournit exactement ces opérations sur un graphe orienté. Les termes de provenance en semi-anneau (`provenance.py`), miroir du modèle Lean, restent la source de vérité du support et de la confiance.

#### Tâches proposées

- Représenter faits et sources comme nœuds d'un `networkx.DiGraph` (arête prémisse → conclusion).
- Invalidation : `nx.descendants` depuis la source retirée, au lieu de réévaluer chaque fait.
- Explication : parcours du graphe (arbre des prémisses) ; garder le rendu texte actuel.
- Exposer le graphe de provenance (export GraphML ou JSON node-link dans le rapport M0), utile au chatbot et à Graphify.
- Vérifier que l'invalidation par graphe coïncide avec l'évaluation booléenne de la provenance (propriété P10/P11) par un test Hypothesis.

#### Critères d'acceptation

- L'ensemble des faits invalidés est identique à celui d'aujourd'hui sur tous les tests (révision par mesure, réfutation d'hypothèse).
- Le rapport M0 contient le graphe de provenance exporté.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/epistemics/knowledge.py`
- `pyproject.toml`
- `tests/property/`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)
