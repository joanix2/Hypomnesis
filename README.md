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

## État

Phases 0 (fondations) et 1 (langage minimal) du plan d'implémentation :
parser LALR, inférence Hindley-Milner, types algébriques, records, modules, filtrage,
interpréteur avec appels terminaux, prélude écrit en Hypomnesis, REPL, contrats JSON Schema
de l'enveloppe de message et du manifeste d'extension.

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
