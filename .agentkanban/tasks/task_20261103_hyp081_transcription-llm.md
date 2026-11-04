---
title: "HYP-081 · Transcription langage naturel → programme Hypomnesis"
lane: qa
created: 2026-11-03T17:42:26+01:00
updated: 2026-11-03T17:42:26+01:00
description: "P1 · L · Phase 7 — Intégration LLM · dépend de HYP-080"
priority: P1
tags: [llm, python]
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

### agent

Plan/todo/implémentation : réutiliser `Codegen.translation`, déjà doté du
catalogue, des réponses simulées et des réparations bornées. L'ADR 0012
et l'adoption du client Ollama supersèdent l'ancien emplacement et la
mention historique d'Anthropic ; aucun réseau n'est nécessaire ici.

Corriger la frontière compilation/exécution : `check` doit vérifier
statiquement M2/M1, sans évaluer les définitions du candidat. Une simulation
reste un callback explicitement choisi par l'hôte, jamais une étape
implicite de vérification. Refuser les budgets de réparation invalides.
Tester la demande MVP avec la réponse Hypomnesis figée existante, les
diagnostics de typage et l'épuisement du budget, sans Python généré.

### user

### agent

Terminé, validation complète verte ; 20 tests de transcription ciblés.
Le catalogue alimente déjà la réparation bornée : cette itération sécurise
sa frontière statique et les budgets. M2/M1 ne sont pas évalués pendant
`translation.check` (seul le prélude de confiance est initialisé).
Un candidat contenant une division par zéro peut être typé sans l'exécuter ;
cela ne lui confère aucune garantie d'exécution ou d'autorisation.

Demande MVP vérifiée avec le programme figé `plaque_120x80.hyp`, modèle
de test explicitement nommé fixture. Aucune revendication d'appel LLM réel.
Réponses Python refusées ; diagnostics de typage, réparations, échec final
et budgets invalides testés sans réseau. Les grades épistémiques relèvent
de HYP-082, pas d'une acceptation de typage.
QA, validation humaine requise pour done.

### user
