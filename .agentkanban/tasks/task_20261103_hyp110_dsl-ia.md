---
title: "HYP-110 · DSL IA : un langage pour construire des IA"
lane: hypothese
created: 2026-11-03T17:50:18+01:00
updated: 2026-11-04T19:36:05+01:00
description: "P2 · L · Instances de domaines · dépend de HYP-046, HYP-056 · idée à planifier"
priority: P2
tags: [dsl, ia, idee]
---

## Conversation

### user

**Ticket** HYP-110 · **Priorité** P2 · **Taille** L · **Epic** Instances de domaines · **Dépend de** HYP-046, HYP-056 · **Labels** idée, dsl

#### Idée

Une instance de DSL (niveau M2) pour décrire et construire des systèmes d'IA : données, modèles, entraînement, évaluation, agents. Le domaine ne doit demander **aucune modification du noyau** (hypothèse H1).

#### Pistes de conception

- **Concepts** : jeux de données et leurs partitions (entraînement, validation, test), caractéristiques, couches et architectures, modèles, métriques, pipelines ; agents LLM avec outils, politiques et permissions.
- **Formes de tenseurs au niveau des types** : une couche `Linear(n, m)` est une fonction `Tensor[n] -> Tensor[m]`, ce qui rend les incompatibilités de formes impossibles à la compilation. Le mécanisme est celui des dimensions physiques (HYP-056), puis les types dépendants du niveau méta (note M3).
- **Architectures comme compositions** : une architecture est une composition de morphismes typés ; une théorie « réseau » (HYP-046) a pour modèles PyTorch, scikit-learn, etc.
- **Entraînement comme effet** : il est décrit comme une valeur et exécuté par un handler (HYP-060) ; simulation, dry-run et production restent possibles.
- **Épistémique** : toute prédiction a le support `Estimated`, avec le modèle, sa version et les données d'entraînement dans sa provenance (HYP-031).
- **Rôle transversal** : ce DSL fournit les **estimateurs** des autres domaines, par exemple l'épaisseur de plaque en CAO ou une quantité manquante dans un dossier DREAL.

#### Propriétés prouvables envisagées

- **Absence de fuite de données** : le jeu de test n'influence ni l'entraînement ni le réglage. C'est une propriété de flux d'information, lisible sur les termes de provenance.
- Cohérence des formes de toute architecture bien typée.
- Intégrité de l'évaluation : une métrique publiée est calculée sur des données jamais vues par le modèle.

#### Questions ouvertes

- Périmètre initial : ML classique (scikit-learn), réseaux de neurones (PyTorch), ou agents LLM ?
- Faut-il décrire les agents (outils, permissions) ici, ou dans le DSL Applications ?

#### Références

- `docs/architecture/m3-metalangage.md` (§4.4 capacités, §6.1 modèles de théories)
- `docs/verification/proprietes.md`
- Conventions : `.agentkanban/memory.md`

### agent

Reclassement demandé par l'utilisateur : `todo` → `hypothese`. Cette idée
de DSL IA conserve ses pistes et questions de périmètre ; elle n'est pas
une architecture adoptée ni une implémentation à lancer automatiquement.
Priorité et dépendances conservées.

### user
