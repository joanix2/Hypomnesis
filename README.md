# Hypomnesis

*A language for programmable knowledge and reasoning.*

Hypomnesis est un métalangage fonctionnel à syntaxe OCaml destiné à définir des DSL métiers :
concepts, connaissances, règles, contraintes, et capacités d'action contrôlées. Il ne remplace
ni les solveurs, ni les bibliothèques scientifiques : il fournit un langage typé pour les
décrire, les composer et contrôler leurs interactions.

- Spécification : [docs/specification/cahier-des-charges-v0.2.md](docs/specification/cahier-des-charges-v0.2.md)
- Architecture et avancement : [docs/architecture/overview.md](docs/architecture/overview.md)
- Référence du langage : [docs/language/reference.md](docs/language/reference.md)
- Décisions d'architecture : [docs/adr/](docs/adr/README.md)
- Vérification formelle (Lean 4) : [docs/verification/proprietes.md](docs/verification/proprietes.md), preuves dans [formal/](formal/README.md)

## État

Phases 0 (fondations) et 1 (langage minimal) du plan d'implémentation :
parser LALR, inférence Hindley-Milner, types algébriques, records, modules, filtrage,
interpréteur avec appels terminaux, prélude écrit en Hypomnesis, REPL, contrats JSON Schema
de l'enveloppe de message et du manifeste d'extension.

## Démonstrateur MVP

Le scénario du cahier des charges (§16.2), de bout en bout :

```bash
hypomnesis demo plaque                              # dry-run : rien n'est exporté
hypomnesis demo plaque --mode production --mesure 5 # export SVG/JSON, puis révision par une mesure
hypomnesis demo plaque --estimateur abaque --masse-max 0.2
hypomnesis demo plaque --sans-permission --mode production
hypomnesis demo ventilation             # §16.3 : capteur → règle → actionneur → capteur
hypomnesis demo ventilation --panne     # l'effet attendu est réfuté, l'hypothèse retirée
```

Demande en français → programme Hypomnesis typé → connaissances avec provenance → épaisseur
estimée (estimateurs interchangeables) → résolue par Z3 (solution revérifiée) → validée par les
règles du domaine écrites en Hypomnesis → export contrôlé (contrat, permission, contraintes,
mode) → rapport expliquant chaque conclusion, journal, traces. Domaine :
`src/hypomnesis/demos/plaque/domaine.hyp`.

## Démarrage

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'

hypomnesis run examples/basics/tour.hyp
hypomnesis run examples/mechanics/units.hyp examples/mechanics/plate.hyp
hypomnesis check examples/mechanics/units.hyp examples/mechanics/plate.hyp
hypomnesis repl
```

Exemple (§4.2 du cahier des charges) — les unités sont une bibliothèque, pas une
connaissance du noyau :

```ocaml
module Mechanics = struct
  type plate = { width : Length.t; height : Length.t; thickness : Length.t option }
  let area p = Length.multiply p.width p.height
end
```

```text
val Mechanics.area : Mechanics.plate -> Area.t = <fun>
```

Mélanger les dimensions est refusé avant l'exécution :

```text
<input>:1:39: type error: This argument has type Area.t but an expression was expected of type Length.t
  let bad = Length.add (Length.mm 1.0) (Mechanics.area plate)
                                        ^^^^^^^^^^^^^^^^^^^^
```

## Développement

```bash
pytest                    # tests unitaires, propriétés (Hypothesis), contrats
ruff check . && ruff format --check .
pyright
```
