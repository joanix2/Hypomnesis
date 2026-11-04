---
title: "HYP-141 · Jeu de données de distillation validé par le compilateur"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P2 · M · Phase 7 — Intégration LLM · dépend de HYP-139, HYP-140"
---

## Conversation

### user

**Ticket** HYP-141 · **Priorité** P2 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-139, HYP-140 · **Labels** python, llm, fine-tuning, idée

#### Contexte

Première étape de la branche fine-tuning : un grand modèle (professeur) produit des paires demande → programme, et le compilateur filtre celles qui sont fausses. On obtient ainsi des données d'entraînement vérifiées, à partir d'un langage.

#### Tâches proposées

- Générer des programmes valides et leurs demandes en français, avec un grand modèle ; varier le vocabulaire, les unités et les cas d'informations manquantes.
- Garder uniquement les paires qui passent le typage et la simulation ; enregistrer modèle, prompt et version du langage pour chacune.
- Séparer entraînement et validation, en excluant le jeu réservé de HYP-139, y compris ses quasi-doublons.
- Vérifier les licences des modèles utilisés : leur sortie peut-elle servir à en entraîner un autre ?

#### Critères d'acceptation

- Le jeu de données est régénérable à partir d'une commande et d'une graine (hors variabilité du modèle).
- 100 % des paires conservées compilent et s'exécutent en simulation.
- Un échantillon relu à la main mesure le taux de demandes dont le programme ne correspond pas au sens, ce que le typage ne détecte pas.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- Conventions et définition de fini : `.agentkanban/memory.md`
