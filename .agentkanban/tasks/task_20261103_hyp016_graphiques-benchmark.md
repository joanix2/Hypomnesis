---
title: "HYP-016 · Banc LLM : graphiques matplotlib"
lane: todo
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-03T21:36:21+01:00
description: "P2 · S · Fondations et gouvernance · dépend de HYP-002 · migration vers bibliothèque"
---

## Conversation

### user

**Ticket** HYP-016 · **Priorité** P2 · **Taille** S · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, llm, matplotlib

#### Contexte

Le banc `hypomnesis benchmark-llm` produit un tableau Markdown. Des graphiques rendent la comparaison des modèles immédiate (hypothèse H2).

#### Tâches proposées

- Générer avec **matplotlib** : exactitude par niveau (parsé, typé, correct, exécuté) par modèle ; latence et jetons générés par modèle ; taux de réussite par cas.
- Écrire les figures (PNG et SVG) à côté du résumé dans `sortie/benchmark-llm/`.
- Option `--sans-graphiques` pour les environnements sans affichage (backend `Agg` par défaut).

#### Critères d'acceptation

- Un lot de résultats JSON existant suffit à régénérer les figures (`hypomnesis benchmark-llm --graphiques resultats.json`).
- Tous les tests existants passent sans modification de leurs attentes.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/llm/benchmark.py`
- `src/hypomnesis/cli.py`
- `pyproject.toml`

#### Références

- Ticket de coordination : HYP-007
- Conventions et définition de fini : `.agentkanban/memory.md` (« bibliothèques plutôt que code maison »)

