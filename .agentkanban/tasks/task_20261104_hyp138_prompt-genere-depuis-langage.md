---
title: "HYP-138 · Générer le prompt LLM depuis la description du langage"
lane: todo
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T08:56:00+01:00
description: "P1 · M · Phase 7 — Intégration LLM · dépend de HYP-080, HYP-137, HYP-139"
---

## Conversation

### user

**Ticket** HYP-138 · **Priorité** P1 · **Taille** M · **Epic** Phase 7 — Intégration LLM · **Dépend de** HYP-080, HYP-137, HYP-139 · **Labels** python, llm

#### Contexte

`system_prompt` colle aujourd'hui le source complet du langage dans le prompt : le LLM voit les règles internes et peut appeler des procédures qui ne devraient pas être exposées, comme l'a montré le cas m11 du banc. Le compilateur doit produire le prompt à partir des signatures et des descriptions.

#### Tâches proposées

- Compiler un langage vers un prompt : syntaxe utile, types, champs, unités, procédures publiques, chacun avec sa description.
- Sortie déterministe, avec un budget de taille mesuré et affiché.
- Aucun texte propre à un domaine dans le moteur : tout provient du langage.
- Remplacer le prompt actuel dans `translation.py`, après comparaison au banc.

#### Critères d'acceptation

- Le prompt généré ne contient ni le corps des fonctions ni les éléments non publics.
- Un nouveau langage obtient son prompt sans aucun code spécifique.
- Au banc, le prompt généré fait au moins aussi bien que le prompt actuel sur les mêmes modèles et les mêmes cas, tout en étant plus court.

#### Fichiers concernés

- `src/hypomnesis/llm/translation.py`
- `src/hypomnesis/llm/benchmark.py`

#### Références

- Alimente HYP-081 (transcription)
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

**Avancement (2026-11-04).** Fait : `llm/describe.py` + gabarit Jinja2 compilent un langage en catalogue (types déduits par le typeur, descriptions, balises ; seuls les éléments documentés ; sortie déterministe ; repli sur le source si le langage ne documente rien). Le défaut de `translate` est maintenant `catalogue+rag5`.

Critères : pas de corps de fonction ni d'élément non public ✓ (`test_undocumented_items_stay_out_of_the_catalogue`) ; un nouveau langage obtient son prompt sans code spécifique ✓ (`test_catalogue_is_generic_across_languages`) ; au banc, au moins aussi bon et plus court ✓ : qwen3:4b-instruct 98 % contre 85 % au premier essai, prompt 25 % plus court (détail dans l'ADR 0009).

Reste : la commande `hypomnesis describe` (export JSON et Markdown, HYP-080) et l'affichage du budget de taille.

### user
