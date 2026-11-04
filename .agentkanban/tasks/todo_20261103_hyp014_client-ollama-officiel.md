---
title: "HYP-014 · TODO"
lane: doing
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T15:00:00+01:00
description: "Checklist de HYP-014"
priority: P1
tags: [dette, llm, python]
---

# Iteration 1

État des lieux (vérifié) : `src/hypomnesis/llm/ollama.py` (74 lignes) contient `LLMError`, `Reply(text, seconds, output_tokens, tokens_per_second)` et `OllamaClient` : `_post` en `urllib` (`/api/chat`, erreurs réseau → `LLMError`), `chat(model, messages, *, num_ctx=16384)` (ajoute ` /no_think` au dernier message utilisateur des `qwen3*`, `think: False`, `temperature: 0`, `num_ctx`, durées `eval_count`/`eval_duration`), `models()` (`/api/tags`). Consommateurs : `llm/translation.py` (`Reply`, `client.chat(model, messages)`), `cli.py::_benchmark` (`OllamaClient()`), `tests/unit/test_llm.py` (faux client qui rend `Reply(...)`). Le paquet `ollama` n'est **pas** installé.

Interface à ne pas changer : `OllamaClient()`, `chat`, `models`, `Reply`, `LLMError`. Fichiers : `src/hypomnesis/llm/ollama.py`, `tests/unit/test_ollama_client.py` (nouveau). Aucun conflit avec les autres lots (`cli.py` n'est pas modifié). Ne PAS toucher `pyproject.toml` (Lot 0 ; groupe `llm` + `dev`).

**Interdit : aucun appel à un vrai serveur Ollama ni au GPU.** Les tests utilisent un transport HTTP simulé.

Risque : le critère « le banc donne des résultats comparables » ne peut pas être vérifié sans GPU ; à laisser à l'utilisateur (voir la dernière case).

- [x] Lire l'API du paquet installé (`ollama.Client`, `chat`, `list`, types `ChatResponse`) et noter la version retenue dans le ticket
- [x] Test de caractérisation avec un faux serveur : à partir d'un `httpx.MockTransport` passé au client officiel (arguments httpx transmis par `ollama.Client(host=…, timeout=…, transport=…)`), vérifier le corps envoyé : modèle, messages, `stream: False`, `think: False`, `options.temperature = 0`, `options.num_ctx`
- [x] Réécrire `chat` et `models` au-dessus de `ollama.Client` ; `Reply` calculé depuis `eval_count` et `eval_duration` comme aujourd'hui (jetons/s = 0 si durée nulle)
- [x] Conserver le contournement Qwen3 : `/no_think` ajouté uniquement au dernier message `user` des modèles `qwen3*`, sans modifier la liste passée par l'appelant
- [x] Erreurs : `ollama.ResponseError`, `ConnectionError`, `httpx.TimeoutException` → `LLMError` avec le message « Ollama injoignable (URL) : … » ; erreur renvoyée par le serveur → `LLMError`
- [x] Préparer les sorties structurées : paramètre optionnel `format: dict | None` (schéma JSON) transmis au champ `format`, non utilisé par défaut ; un test vérifie la transmission
- [x] Séparer le temps de chargement du modèle du temps total (`load_duration` de la réponse) dans `Reply` avec une valeur par défaut, sans casser le faux client des tests (HYP-139 en profitera)
- [x] Vérifier que `tests/unit/test_llm.py` passe inchangé
- [ ] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa` (rapide : ruff/tests rouges à cause de fichiers d'autres agents ; `complet` à relancer en fin de lot)
- [x] Note dans la fiche : la comparaison « même modèle, même jeu » est à lancer par l'utilisateur sur sa machine (`hypomnesis benchmark-llm`) ; ne pas la lancer ici
