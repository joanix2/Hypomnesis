---
title: "HYP-006 · Migrer la CLI d'argparse vers Typer"
lane: qa
created: 2026-11-03T21:28:04+01:00
updated: 2026-11-04T14:45:00+01:00
description: "P2 · M · Fondations et gouvernance · dépend de HYP-002"
---

## Conversation

### user

**Ticket** HYP-006 · **Priorité** P2 · **Taille** M · **Epic** Fondations et gouvernance · **Dépend de** HYP-002 · **Labels** python, cli

#### Contexte

La CLI (`src/hypomnesis/cli.py`) est écrite avec `argparse`. Elle a grossi (`run`, `check`, `repl`, `lancer`, `benchmark-llm`) et la construction des parseurs occupe une bonne part du fichier. Typer déclare chaque commande comme une fonction annotée, génère une aide lisible (rendu Rich) et valide les options par leur type. Rich servira aussi aux rapports du chatbot neurosymbolique.

#### Tâches proposées

- Ajouter `typer` aux dépendances (`pyproject.toml`) ; noter dans le ticket la version retenue et ce qu'elle apporte (Click, Rich).
- Réécrire chaque commande comme une fonction annotée : chemins avec `Path` (existence vérifiée), `--mode` en `Enum`, options répétables (`--env`) en listes.
- Conserver **à l'identique** les noms de commandes et d'options, les sorties et les codes de retour (0, 1, 64), y compris les messages d'erreur positionnés (`ParseError`, `TypeCheckError`…).
- Garder `main(argv)` appelable depuis les tests, et le point d'entrée `hypomnesis` de `pyproject.toml`.
- Mettre à jour `scripts/validate.sh` (il appelle `python -m hypomnesis.cli`), `README.md` et `TECHNICAL.md` si des invocations changent.

#### Critères d'acceptation

- Tous les tests existants de la CLI passent sans modification de leurs attentes (`tests/unit/test_examples.py`, `tests/unit/test_certificate.py`, `tests/integration/test_languages.py`, `tests/unit/test_llm.py`).
- `hypomnesis --help` et l'aide de chaque commande sont générées par Typer et lisibles.
- Un chemin inexistant ou un mode inconnu est refusé avec un message clair, avant tout chargement.
- `./scripts/validate.sh complet` vert.

#### Fichiers concernés

- `src/hypomnesis/cli.py`
- `pyproject.toml`
- `scripts/validate.sh`

#### Références

- `TECHNICAL.md` (commandes)
- Conventions et définition de fini : `.agentkanban/memory.md`

### agent

**Fait** (commit `1d65842`, `./scripts/validate.sh complet` vert) :

- `src/hypomnesis/cli.py` : `app = typer.Typer(...)`, une fonction annotée par commande (`run`, `check`, `repl`, `lancer`, `decrire`, `benchmark-llm`) et `--version` (option eager). Mêmes noms d'options et défauts ; `--mode` est l'énumération `Mode`, `--format` l'énumération `Format`, `--env` une `list[str]` répétable ; aides en français. Imports lourds toujours paresseux. `main(argv) -> int` conservé ; le point d'entrée `hypomnesis = "hypomnesis.cli:main"` et `python -m hypomnesis.cli` fonctionnent sans changement (`pyproject.toml` non modifié).
- `tests/unit/test_cli_contract.py` (nouveau) : codes de sortie (0, 1, 64, usage), `--version`, `--env` répété, `--mode` inconnu, langage absent → 1 + `refusé : …`, certificat. Les cas déjà valides sous argparse l'étaient avant la migration ; seul « fichier `.hyp` absent » est une amélioration (voir écarts).
- `TECHNICAL.md` : ligne « CLI » et nouvelle sous-section « CLI (Typer, HYP-006) » (codes de sortie, énumérations, règle sur le dossier langage). `README.md` et `scripts/validate.sh` n'ont pas d'invocation à changer.
- Version retenue : **Typer 0.27.3** (+ Rich 15.0.0). Apport : aide rendue par Rich, options validées par leur type (`Path`, `Enum`, `int`), erreurs d'usage encadrées. Particularité : Typer 0.27 **embarque** Click (`typer._click`), le paquet `click` n'est plus installé ; le code n'importe donc pas `click`.

**Écarts au plan**

- `main` appelle `app(...)` en mode autonome (`standalone_mode=True`) et capte le `SystemExit`, au lieu de `standalone_mode=False` + conversion des exceptions Click : cela évite d'importer des classes Click (privées dans Typer 0.27, publiques dans les versions < 0.27 couvertes par `typer>=0.12`) et garde le rendu Rich des erreurs.
- Un fichier `.hyp` absent (`run`/`check`) ou un programme absent (`lancer`) sort désormais avec le code d'usage **2** et un message Rich, avant tout chargement ; avant, c'était une trace `FileNotFoundError`. Aucun test existant ne l'attendait. Idem pour les dossiers de `benchmark-llm` (`exists=True, file_okay=False`), ajouté par cohérence avec le critère « chemin inexistant refusé avant tout chargement ».
- Le dossier langage de `lancer`/`decrire` n'a pas `exists=True` (décision utilisateur) : code 1 et `refusé : …` conservés. Conséquence : si le programme `.hyp` de `lancer` est lui-même absent, Click répond (code 2) avant que le langage soit examiné.
- Aide : les libellés de `--mode`/`--format`/`--sortie` (benchmark) ont reçu un texte français, avant absent. Avant/après comparés : aucune option perdue. `--help` est affiché par Click en anglais (« Show this message and exit »).
- `benchmark-llm` : seule l'aide et l'analyse des options ont été exercées ; aucun appel Ollama/GPU.

**Points de vigilance** : HYP-016 ajoute une option à `benchmark-llm` : elle suit le même schéma (paramètre annoté dans `benchmark_command` + argument de `_benchmark`). `repl` vérifié à la main (échange `;;`, erreur de syntaxe positionnée, Ctrl-D → 0). Les autres modifications non commitées de l'arbre (certify, llm, kanban…) appartiennent à d'autres agents et n'ont pas été touchées.

### user
