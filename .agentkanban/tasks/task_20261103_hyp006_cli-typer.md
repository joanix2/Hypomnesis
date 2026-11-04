---
title: "HYP-006 · Migrer la CLI d'argparse vers Typer"
lane: todo
created: 2026-11-03T21:28:04+01:00
updated: 2026-11-03T21:28:04+01:00
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
