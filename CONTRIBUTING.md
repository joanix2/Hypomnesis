# Contribuer à Hypomnesis

Merci de votre intérêt. Les contributions sont bienvenues : correctifs, tests, documentation,
nouveaux langages métier et exemples.

## Avant de commencer

- Ouvrez une issue pour un changement de fond (syntaxe, sémantique, architecture), afin de le
  discuter avant d'écrire du code. Les décisions d'architecture passent par une ADR dans
  [docs/adr/](docs/adr/README.md).
- Le moteur (`src/hypomnesis/`) ne contient aucun concept de domaine : ce qui est propre à un
  métier va dans un langage de niveau M2 (`demo/languages/`). Un test d'architecture le vérifie.

## Mise en place

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
```

## Avant d'ouvrir une demande de fusion

```bash
pytest
ruff check . && ruff format --check .
pyright
```

La validation complète, preuves Lean et vérificateur de certificats compris, se lance avec
`./scripts/validate.sh complet` sur Linux et macOS (Python ≥ 3.11, dépendances `dev` et
version Lean indiquée dans `formal/lean-toolchain` nécessaires).

Ne contournez pas un validateur (`noqa`, `type: ignore`, test désactivé, `sorry` dans les
preuves Lean) : corrigez la cause.

## Licence des contributions

Hypomnesis est distribué sous licence MIT (voir [LICENSE](LICENSE)). En soumettant une
contribution, vous acceptez qu'elle soit publiée sous cette même licence, et vous confirmez en
avoir le droit. Il n'y a pas de contrat de licence de contributeur à signer.

## Modèles de langage

Le dépôt ne contient aucun poids de modèle. Les modèles Qwen, Gemma ou autres utilisés pour les
bancs d'essai sont soumis à leurs propres conditions d'utilisation : vérifiez-les avant d'en
redistribuer les sorties, notamment pour entraîner un autre modèle.
