---
title: "HYP-006 · TODO"
lane: todo
created: 2026-11-04T15:00:00+01:00
updated: 2026-11-04T15:00:00+01:00
description: "Checklist de HYP-006"
---

# Iteration 1

État des lieux (vérifié) : `src/hypomnesis/cli.py` (244 lignes) construit les parseurs `argparse` de `run`, `check` (`--emit-certificate`), `repl`, `lancer` (`--demande`, `--mode`, `--sortie`, `--env` répétable, `--sans-permission`), `decrire` (`--format`), `benchmark-llm` (`--modeles`, `--reparations`, `--strategie`, `--jeux`, `--sortie`…). `main(argv) -> int` est appelé directement par les tests : `test_examples.py` (`run`/`check`, retour 0 et 1), `test_certificate.py` (`check --emit-certificate`), `test_describe.py` (`decrire`, un langage absent rend **1**), `test_languages.py` (`lancer … --env panne=1`). `validate.sh` ligne 57 appelle `python -m hypomnesis.cli check … --emit-certificate` (le bloc `if __name__ == "__main__"` doit rester). Typer et Rich ne sont **pas** installés dans `.venv`.

Pré-requis : Lot 0 de HYP-007 (dépendances dans `pyproject.toml`, `pip install -e '.[dev]'`). Fichiers : `src/hypomnesis/cli.py`, `README.md`, `TECHNICAL.md` (ligne « CLI »). Ne PAS toucher `pyproject.toml` ici. **HYP-016 vient après** (il ajoute une option à `benchmark-llm` dans ce même fichier) ; HYP-010 et HYP-130 aussi touchent `cli.py`.

Risque principal : Typer/Click sortent avec le code **2** sur une erreur d'usage et lèvent `SystemExit`, alors que les tests attendent un `int` retourné et **1** pour un langage absent.

- [ ] Écrire un test de caractérisation `tests/unit/test_cli_contract.py` AVANT la migration : codes de retour de chaque commande (0, 1, 64), `--version`, `--env a=1 --env b=2`, `--mode` inconnu rejeté ; il doit passer sur argparse puis sur Typer
- [ ] Capturer la sortie de `hypomnesis --help` et de chaque `<commande> --help` (avant), pour comparer les noms d'options après
- [ ] `app = typer.Typer(...)`, une fonction annotée par commande, mêmes noms de commandes et d'options (`--emit-certificate`, `--sans-permission`, `--env` en `list[str]`, `--mode` en `Enum` : simulate, dry-run, production, `--format` en `Enum` md|json)
- [ ] Chemins : `Path` avec `exists=True` pour les fichiers `.hyp` de `run`/`check` (refus clair avant tout chargement, code d'usage de Click). **Ne pas** mettre `exists=True` sur `langage` de `lancer`/`decrire` : les tests attendent le code 1 et le message `refusé : …` de `LanguageError`
- [ ] Garder `def main(argv: list[str] | None = None) -> int` : appeler `app(args=argv, standalone_mode=False)`, convertir `click.exceptions.Exit`/`UsageError`/`Abort` en entier retourné, ne jamais laisser `SystemExit` sortir de `main`
- [ ] Conserver à l'identique les messages positionnés (`HypomnesisError.render`), le code 64 de `lancer` sans programme, et la sortie sur stdout/stderr (les tests lisent `capsys`)
- [ ] Imports paresseux conservés (`llm`, `certify` dans les fonctions) pour ne pas ralentir `check`
- [ ] `--version` conservé (`typer.Option(callback=…, is_eager=True)`)
- [ ] `repl` : conserver le comportement interactif ; vérifier à la main un échange `;;` et Ctrl-D
- [ ] Comparer l'aide avant/après : aucune option perdue ; aide rendue par Rich lisible
- [ ] Tests existants inchangés dans leurs attentes : `pytest tests/unit/test_examples.py tests/unit/test_certificate.py tests/unit/test_describe.py tests/integration/test_languages.py tests/unit/test_llm.py`
- [ ] `./scripts/validate.sh rapide` (avant chaque commit) ; Ruff n'autorise ni `noqa` ni `type: ignore` : annoter correctement pour Pyright
- [ ] `README.md` et `TECHNICAL.md` : invocations et ligne « CLI » à jour ; noter dans le ticket la version de Typer retenue et ce qu'elle apporte (Click, Rich)
- [ ] `./scripts/validate.sh complet`, commit en français, mettre la tâche en `qa`
