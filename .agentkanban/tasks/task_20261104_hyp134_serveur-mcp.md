---
title: "HYP-134 · Serveur MCP pour les LLM"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · M · Outillage et visualisation · dépend de HYP-133"
---

## Conversation

### user

**Ticket** HYP-134 · **Priorité** P1 · **Taille** M · **Epic** Outillage et visualisation · **Dépend de** HYP-133 · **Labels** python, llm, mcp

#### Contexte

Exposer les langages à n'importe quel client compatible MCP, sans intégration propre à chaque client. Le LLM reste un simple traducteur (§14) : le serveur ne doit pas lui ouvrir une voie vers les actionneurs réels.

#### Tâches proposées

- Serveur basé sur le SDK Python officiel `mcp`, en transport stdio.
- Outils : lister les langages, décrire un langage, vérifier un programme, le simuler (`simulate`, `dry-run`).
- Ressources : description du langage, exemples.
- Aucun mode `production` dans ce ticket ; l'ouvrir plus tard passera par les permissions de HYP-062.

#### Critères d'acceptation

- Un client MCP réel traduit une demande du banc mécanique en programme accepté, en utilisant uniquement ces outils.
- Aucun outil exposé ne peut déclencher un actionneur réel ; un test le vérifie.
- Les erreurs renvoyées sont les diagnostics structurés de HYP-130.

#### Fichiers concernés

- `src/hypomnesis/mcp/`
- `pyproject.toml`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`
