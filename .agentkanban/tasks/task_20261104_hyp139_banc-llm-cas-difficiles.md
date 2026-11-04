---
title: "HYP-139 · Banc LLM : cas difficiles et jeu de test réservé"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · S · Phase 7 — Intégration LLM · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-139 · **Priorité** P1 · **Taille** S · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-002 · **Labels** python, llm, tests

#### Contexte

Trois modèles sur quatre font 12/12 aux cas mécaniques : le banc sature et ne peut plus mesurer un gain. Il faut des cas plus difficiles avant de juger le prompt généré, le mini-RAG ou le fine-tuning (HYP-138, HYP-140, HYP-142).

#### Tâches proposées

- Cas plus difficiles : plusieurs conversions, formulations indirectes, informations manquantes ou contradictoires, choix entre procédures proches, cas de ventilation.
- Séparer un jeu de test réservé, jamais utilisé comme exemple ni pour l'entraînement.
- Répéter les essais et publier les intervalles de confiance ; compter à part le temps de chargement du modèle.
- Corriger le faux négatif de m11 : un record écrit directement dans l'appel est correct même sans variable `demande`.

#### Critères d'acceptation

- Sur le nouveau jeu, aucun des modèles actuels n'atteint 100 % au premier essai, sinon ajouter d'autres cas difficiles.
- Le rapport distingue typé, correct, réparations et temps sans chargement.
- Un test vérifie que le jeu réservé et les exemples ne se recoupent pas.

#### Fichiers concernés

- `src/hypomnesis/llm/benchmark.py`
- `languages/mecanique/benchmark.json`
- `languages/ventilation/benchmark.json`

#### Références

- Lié à HYP-083 (demandes ambiguës)
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

**Avancement (2026-11-04).** Fait : trois jeux de cas (`dev` 15, `test` 20 réservé, `hard` 20 : nombres en lettres, ordre largeur/hauteur inversé, unités mixtes, négation de la mesure…), option `--jeux`, métrique **correct au premier essai**, faux négatif de m11 corrigé (un record écrit dans l'appel vaut la variable `demande`), test de non-recoupement entre exemples et cas.

Critère « aucun modèle n'atteint 100 % au premier essai » : tenu pour qwen3:4b-instruct (96-98 %) et qwen3.5:9b (98 %) sur les 55 cas ; qwen3:14b et gemma4:12b ne sont pas remesurés sur `hard`.

Reste : répétitions avec intervalles de confiance (à température 0 les essais sont déterministes : il faut soit une température > 0, soit des intervalles de Wilson sur les cas) et temps de chargement compté à part.

### user


