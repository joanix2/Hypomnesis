---
title: "HYP-014 · Client LLM : remplacer le client urllib par le paquet officiel ollama"
lane: doing
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P1 · S · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
priority: P1
tags: [dette, llm, python]
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

### agent

`src/hypomnesis/llm/ollama.py` est réécrit au-dessus du paquet officiel `ollama` (0.6.3, httpx 0.28.1, déjà installé via l'extra `llm`). Interface conservée : `OllamaClient()`, `chat(model, messages, *, num_ctx=…)`, `models()`, `Reply`, `LLMError` ; `translation.py`, `benchmark.py`, `cli.py` et `tests/unit/test_llm.py` sont inchangés.

- **Réécriture** : `ollama.Client(host, timeout, transport)` ; `Reply` est calculé depuis `eval_count`/`eval_duration` (jetons/s = 0 si durée nulle). Options inchangées (`temperature 0`, `num_ctx`, `think False`, `stream False`). `/no_think` reste ajouté au dernier message `user` des `qwen3*`, sans modifier la liste de l'appelant.
- **Ajouts** : `chat(..., num_predict=None, format=None)` (schéma JSON transmis au champ `format`, non utilisé par défaut) ; `Reply.load_seconds` (défaut `0.0`, depuis `load_duration`) ; `OllamaClient(..., transport=None)` pour injecter un transport httpx simulé.
- **Erreurs** : `ollama.ResponseError` → `LLMError(message du serveur)` ; `ConnectionError` et `httpx.HTTPError` (dont timeouts) → `LLMError("Ollama injoignable (URL) : …")`. Ce dernier cas couvre aussi `models()`, qui n'avait aucune gestion d'erreur avant.
- **Import paresseux** : `ollama` et `httpx` sont importés dans les méthodes, pour que `hypomnesis.llm` (donc `translation.py` et les tests) reste importable sans l'extra `llm`.
- **Tests** : `tests/unit/test_ollama_client.py` (9 tests, `httpx.MockTransport`, aucun réseau ni GPU) : corps envoyé, mesures, `num_predict`/`format`, `/no_think`, erreur serveur, serveur injoignable, timeout, `models()`.
- **Vérifications** : ruff (lint + format) et Pyright (avec `--pythonpath .venv/bin/python`) verts sur mes fichiers ; `pytest` vert hors `tests/tools/test_kanban.py` (3 échecs : `scripts/kanban.py` en cours de modification par un autre agent) et `tests/unit/test_trace.py` (import `trace_context` absent, travail HYP-015 en cours). `./scripts/validate.sh rapide` est donc rouge pour des raisons étrangères à ce ticket.

**Reste / écarts** : pas de commande `complet` (rouge à cause du travail d'autrui) ; la tâche reste en `doing` tant que `pytest` global n'est pas vert. `TECHNICAL.md` n'a pas de section LLM : non modifié. **À faire par l'utilisateur (GPU)** : comparer « même modèle, même jeu de cas » avant/après avec `hypomnesis benchmark-llm` ; je ne l'ai pas lancé. Point de vigilance : `models()` lit désormais le champ `model` de `/api/tags` (au lieu de `name`) ; les deux sont fournis par les serveurs Ollama récents.

### user
