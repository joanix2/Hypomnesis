---
title: "HYP-014 · Client LLM : remplacer le client urllib par le paquet officiel ollama"
lane: todo
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P1 · S · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-014 · **Priorité** P1 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, llm, dette

#### Contexte

`src/hypomnesis/llm/ollama.py` parle à l'API HTTP d'Ollama avec `urllib`. Le paquet Python officiel `ollama` couvre la même API (chat, options, sorties structurées par schéma JSON, flux), avec ses types et sa gestion d'erreurs.

#### Tâches proposées

- Réécrire `OllamaClient.chat` et `models` au-dessus du paquet `ollama`, en gardant l'interface `Reply` (texte, durée, jetons, jetons/s) utilisée par la traduction et le banc.
- Garder le contournement de réflexion des Qwen3 (`think: false` et `/no_think`) et l'extraction robuste du code.
- Préparer les sorties structurées (`format` = schéma JSON) pour le chatbot.

#### Critères d'acceptation

- Le banc `hypomnesis benchmark-llm` donne des résultats comparables (même modèle, même jeu de cas).
- Les tests avec le faux client (`tests/unit/test_llm.py`) passent inchangés.
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/llm/ollama.py`
- `pyproject.toml`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)
