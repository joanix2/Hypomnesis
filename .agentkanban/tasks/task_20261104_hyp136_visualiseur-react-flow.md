---
title: "HYP-136 · Visualiseur de pipelines avec React Flow"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P2 · M · Outillage et visualisation · dépend de HYP-135"
---

## Conversation

### user

**Ticket** HYP-136 · **Priorité** P2 · **Taille** M · **Epic** Outillage et visualisation · **Dépend de** HYP-135 · **Labels** react, visualisation

#### Contexte

Mermaid convient aux diagrammes statiques, mais les pipelines réels demandent de naviguer : zoom, déplacement, détail d'un nœud. React Flow affiche le graphe JSON de HYP-135.

#### Tâches proposées

- Application React et TypeScript dans `tools/visualiseur/`, avec React Flow et une mise en page automatique (ELK ou Dagre).
- Nœuds distincts selon le genre d'étape ; panneau de détail : type, position dans le source, faits produits.
- Commande pour ouvrir le graphe d'un programme dans le navigateur.
- Validation du JSON reçu contre le schéma de HYP-135.

#### Critères d'acceptation

- Le pipeline du scénario de la plaque s'affiche lisiblement, sans placement manuel.
- Un clic sur un nœud montre son type et sa position dans le source.
- Le visualiseur ne contient aucun concept de domaine : le pipeline de ventilation s'affiche sans modification du code.
- Tests des composants et lint TypeScript intégrés à la validation.

#### Fichiers concernés

- `tools/visualiseur/`
- `scripts/validate.sh`

#### Références

- Piste ultérieure : vue dans VS Code (HYP-131), états d'une exécution en direct.
- Conventions et définition de fini : `.agentkanban/memory.md`
