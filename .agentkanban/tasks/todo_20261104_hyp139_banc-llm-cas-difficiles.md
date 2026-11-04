---
title: "HYP-139 · TODO"
lane: todo
created: 2026-11-04T14:50:00+01:00
updated: 2026-11-04T14:50:00+01:00
description: "Checklist de HYP-139"
---

# Iteration 1

Reste à faire (voir l'entrée `### agent` de la fiche) : répétitions avec intervalles de confiance, et temps de chargement compté à part. **Aucun appel à un modèle ni au GPU** : tout se code et se teste avec le faux client de `tests/unit/test_llm.py` et des résultats synthétiques.

État du code : `llm/ollama.py::Reply` porte déjà `load_seconds` (ajouté par HYP-014) ; `llm/benchmark.py::summary` n'affiche pas encore le temps sans chargement ni d'intervalle ; l'appel `chat` fixe `temperature: 0`, donc deux essais d'un même cas sont identiques.

Choix de bibliothèque : pas d'intervalle écrit à la main. `scipy.stats.binomtest(k, n).proportion_ci(method="wilson")` ; SciPy est déjà installé par scikit-learn, le déclarer dans l'extra `llm` et `dev`. Le tableau Markdown de `summary()` reste maison.

Fichiers : `src/hypomnesis/llm/benchmark.py`, `src/hypomnesis/llm/translation.py` et `src/hypomnesis/llm/ollama.py` (paramètre de température), `pyproject.toml` (`scipy`), `tests/unit/test_llm.py`, `tests/unit/test_benchmark.py` (nouveau). **Ne pas** toucher `cli.py` sans vérifier qu'HYP-016 est terminé (il y ajoute `--graphiques`) ; une option `--essais` y sera ajoutée en dernier.

- [ ] Fonction `wilson(k, n, confidence=0.95) -> tuple[float, float]` au-dessus de `scipy.stats.binomtest` ; tests sur des cas connus (0/10, 10/10, 5/10) et `n = 0`
- [ ] `summary()` : afficher les intervalles de Wilson pour « Correct (1er essai) » et « Correct » ; tableau existant inchangé pour le reste
- [ ] Temps sans chargement : somme des `reply.seconds - reply.load_seconds` par cas ; deux colonnes, « Temps moy. » et « Temps moy. hors chargement »
- [ ] Répétitions : paramètre `temperature` (défaut 0) passé de `run_benchmark` à `translate` puis à `ChatClient.chat` ; quand `essais > 1`, la température par défaut des répétitions est > 0 (valeur consignée dans la fiche), et le résumé distingue les essais d'un même cas
- [ ] Faux client : mettre à jour le faux `ChatClient` de `test_llm.py` pour accepter `temperature` (signature compatible, test existant inchangé dans ses attentes)
- [ ] Test : avec un faux client déterministe, `essais=3` produit 3 fois plus de lignes et des intervalles cohérents avec les comptes
- [ ] Test existant de non-recoupement exemples / jeu réservé toujours vert
- [ ] Documenter dans `TECHNICAL.md` (section Banc LLM) : intervalles de Wilson, temps hors chargement
- [ ] Noter dans la fiche que la remesure des modèles reste à faire par l'utilisateur (GPU) ; ne pas la lancer
- [ ] `./scripts/validate.sh rapide`, puis `complet` ; commit en français, mettre la tâche en `qa`
