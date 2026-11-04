---
title: "HYP-139 · Banc LLM : cas difficiles et jeu de test réservé"
lane: doing
created: 2026-11-04T08:56:00+01:00
updated: 2026-11-04T14:56:00+01:00
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

### agent

**Avancement (2026-11-04, seconde passe).** Fait, sans GPU ni appel à Ollama (faux client `FakeLLM`) :

- `llm/benchmark.py` : `wilson(k, n)` (`scipy.stats.binomtest(...).proportion_ci(method="wilson")`) ; `summary()` affiche les IC de Wilson à 95 % pour « Correct (1er essai) » et « Correct », une colonne « Cas réparés » et deux temps (« Temps moy. » et « Temps moy. hors chargement ») ; second tableau `repetition_table` quand des cas sont répétés (correct 1er essai moyen par cas, cas stables). `CaseResult` gagne `load_seconds`, `seconds_without_load`, `repetition`, `temperature` (tous dans le JSON).
- Répétitions au niveau bibliothèque : `run_benchmark(repetitions=N, temperature=T)`, `run_case(temperature=, repetition=)`, `translate(temperature=)`, `OllamaClient.chat(temperature=)` (`ChatClient` protocole mis à jour). `N > 1` sans température explicite → `REPEAT_TEMPERATURE = 0.7` ; un lot simple reste à 0.
- `llm/plots.py` : le calcul de Wilson maison est remplacé par scipy (`wilson_interval`, tests HYP-016 inchangés et verts) ; `normalize` lit `load_seconds`/`seconds_without_load` (anciens lots tolérés) ; la figure de coût trace temps total et hors chargement côte à côte.
- `pyproject.toml` : `scipy>=1.11` ajouté aux extras `llm` et `dev` (uniquement ces deux lignes).
- Tests : `tests/unit/test_benchmark.py` (nouveau : Wilson 0/10, 10/10, 5/10, n=0 ; summary ; JSON ; répétitions ×3 ; plots), `test_ollama_client.py` (température), `FakeLLM` accepte `temperature`. `TECHNICAL.md` : sous-section « Banc LLM : intervalles, temps hors chargement, répétitions (HYP-139) ».
- Commit : le code a été embarqué par erreur dans le commit `d2576a3` (« HYP-040 : fiche mise à jour… ») d'un autre agent, qui a ramassé mon index ; contenu correct, message trompeur.

**À brancher (CLI, hors périmètre : `cli.py` appartient à HYP-130)** : options `--repetitions N` et `--temperature T` de `hypomnesis benchmark-llm`, à passer à `run_benchmark(repetitions=…, temperature=…)` ; le tableau de `summary()` affiche déjà le second tableau de répétitions.

**À vérifier par l'utilisateur (GPU)** : remesure de qwen3:14b et gemma4:12b sur `hard` (critère « aucun modèle à 100 % au 1er essai ») et un lot réel avec `--repetitions` une fois l'option branchée ; non lancé ici.

**Écarts / vigilance.** `./scripts/validate.sh complet` n'a pas été relancé jusqu'au bout (arrêt urgent) ; `rapide` : ruff, format, kanban et tests verts sur ma dernière exécution (un échec lint transitoire venait d'un autre agent, disparu ensuite). `tests/unit/test_llm.py` contient aussi des modifications non commitées d'HYP-137 (`strict=False` dans `test_an_undocumented_language…`), que je n'ai pas incluses. Les colonnes de `summary()` ont changé (« Cas réparés » et « Temps moy. hors chargement » ajoutés) : le préfixe `| Modèle | Cas |` reste.

Reste pour clore : `validate.sh complet` vert, puis passer la fiche en `qa`.

### user
