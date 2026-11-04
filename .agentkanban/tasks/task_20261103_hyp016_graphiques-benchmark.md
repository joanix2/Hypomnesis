---
title: "HYP-016 · Banc LLM : graphiques matplotlib"
lane: qa
created: 2026-11-03T21:36:21+01:00
updated: 2026-11-04T15:10:00+01:00
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

### agent

HYP-016 implémenté (commit `a884a1c`).

- `src/hypomnesis/llm/plots.py` (nouveau) : `load_results`/`normalize` (chargeur tolérant : sans `strategy`/`split`/`correct_first`, on suppose stratégie par défaut, jeu `dev`, « juste au premier essai » = juste avec ≤ 1 tentative) ; séries pures (`accuracy_by_label`, `accuracy_by_split`, `cost_by_label`, `wilson_interval` écrit à la main, scipy inutile) ; trois figures (justesse premier essai / après réparations par modèle·stratégie, idem par jeu dev/test/hard, temps et jetons par cas) écrites en PNG et SVG par `render_all(results, dossier, stem)`. Backend `Agg` ; les figures utilisent `Figure` + `FigureCanvasAgg`, sans `pyplot`.
- CLI : `benchmark-llm --graphiques/--sans-graphiques` (actif par défaut, figures à côté du résumé `resultats-<horodatage>-*.png|svg` ; ignoré avec avertissement si matplotlib est absent) et nouvelle commande `graphiques-llm FICHIER.json [--sortie DIR]` qui régénère les figures sans Ollama.
- Tests : `tests/unit/test_plots.py` (jeu synthétique, 14 cas : Wilson, chargeur ancien format, séries, fichiers PNG/SVG, commande, option avec client factice). `test_cli_contract.py` et `test_llm.py` inchangés et verts. `./scripts/validate.sh rapide` et `complet` verts (un premier `complet` a échoué sur pre-commit pendant qu'un autre agent modifiait des fiches Kanban ; relancé, tout est vert).
- `TECHNICAL.md` : sous-section « Banc LLM : graphiques (HYP-016) ».

Écarts au plan : le critère d'acceptation parlait de `benchmark-llm --graphiques resultats.json` ; `benchmark-llm` exigeant dossiers de langage et `--modeles`, la régénération passe par `graphiques-llm` et `--graphiques` est un booléen (`--sans-graphiques` pour le désactiver). Les « niveaux parsé/typé/correct/exécuté » du ticket ne sont pas tracés : `parsed_first` n'est pas dans le JSON ; seuls justesse (1er essai / après réparations), temps et jetons le sont. `pyproject.toml` non touché (matplotlib déjà déclaré). Figures non versionnées (`sortie/`).

Vigilance : le défaut `--graphiques` actif change légèrement la sortie du banc (6 fichiers en plus). La figure « par jeu » devient large avec beaucoup de stratégies.

### user
