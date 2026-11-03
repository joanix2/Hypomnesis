# Hypomnesis

*A language for programmable knowledge and reasoning.*

Hypomnesis est un métalangage fonctionnel à syntaxe OCaml destiné à définir des DSL métiers :
concepts, connaissances, règles, contraintes, et capacités d'action contrôlées. Il ne remplace
ni les solveurs, ni les bibliothèques scientifiques : il fournit un langage typé pour les
décrire, les composer et contrôler leurs interactions.

- Spécification : [docs/specification/cahier-des-charges-v0.2.md](docs/specification/cahier-des-charges-v0.2.md)
- Bilan MVP (critères du §16.4) : [docs/mvp-bilan.md](docs/mvp-bilan.md)
- Architecture et avancement : [docs/architecture/overview.md](docs/architecture/overview.md)
- Référence du langage : [docs/language/reference.md](docs/language/reference.md)
- Décisions d'architecture : [docs/adr/](docs/adr/README.md)
- Vérification formelle (Lean 4) : [docs/verification/proprietes.md](docs/verification/proprietes.md), preuves dans [formal/](formal/README.md)

## État

Phases 0 (fondations) et 1 (langage minimal) du plan d'implémentation :
parser LALR, inférence Hindley-Milner, types algébriques, records, modules, filtrage,
interpréteur avec appels terminaux, prélude écrit en Hypomnesis, REPL, contrats JSON Schema
de l'enveloppe de message et du manifeste d'extension.

## Niveaux : moteur, langages, programmes, résultats

| Niveau | Dossier | Contenu |
|---|---|---|
| M3 | `src/hypomnesis/` | le moteur : métalangage, typage, runtime, connaissances, effets, solveurs, procédures génériques |
| M2 | `languages/` | des langages métier écrits en Hypomnesis : `mecanique`, `ventilation` |
| M1 | `programs/` | des programmes écrits dans ces langages |
| M0 | `sortie/` | les résultats : rapports, fichiers exportés |

```bash
hypomnesis lancer languages/mecanique programs/mecanique/plaque_120x80.hyp
hypomnesis lancer languages/mecanique programs/mecanique/plaque_120x80.hyp --mode production --observer epaisseur=5
hypomnesis lancer languages/mecanique --demande "Crée une plaque de 200 × 150 mm, masse maximale 1 kg."
hypomnesis lancer languages/mecanique programs/mecanique/plaque_120x80.hyp --estimateur abaque
hypomnesis lancer languages/ventilation programs/ventilation/salle_serveurs.hyp --env panne=1
```

Le scénario du cahier des charges (§16.2) : programme typé → connaissances avec provenance →
inconnue estimée par une fonction du langage → contraintes déclarées dans le langage, résolues
par Z3 et revérifiées → validation par les règles du langage → commande d'export contrôlée
(contrat, permission, contraintes, mode) → rapport, journal, traces, révision. Voir
[ADR 0008](docs/adr/0008-niveaux-m3-m2-m1-m0.md).

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
