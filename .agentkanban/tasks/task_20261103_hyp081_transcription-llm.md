---
title: "HYP-081 · Transcription langage naturel → programme Hypomnesis"
lane: todo
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Phase 7 — Intégration LLM · dépend de HYP-080"
---

## Conversation

### user

**Ticket** HYP-081 · **Priorité** P1 · **Taille** L · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-080 · **Labels** python, llm

#### Contexte

§14.1, §14.3 : le LLM transcrit ; sa sortie est analysée, typée, résolue, validée puis autorisée. Utiliser l'API Claude (consulter la documentation du SDK Anthropic au moment de l'implémentation pour les identifiants de modèle à jour).

#### Tâches proposées

- `llm/transcription.py` : prompt construit à partir de HYP-080 ; boucle de correction alimentée par les diagnostics du compilateur, bornée en nombre d'essais.
- Aucun code Python généré n'est jamais exécuté (§13.5).
- Jeu de tests avec réponses LLM enregistrées (pas d'appel réseau en CI).

#### Critères d'acceptation

- La demande du scénario MVP (§16.2) produit un programme qui passe la vérification de types.
- Une sortie mal typée déclenche une nouvelle tentative avec le diagnostic, puis un échec propre.

#### Fichiers concernés

- `src/hypomnesis/llm/`

#### Références

- `docs/specification/cahier-des-charges-v0.2.md`
- Conventions et définition de fini : `.agentkanban/memory.md`
