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
hypomnesis lancer languages/mecanique programs/mecanique/plaque_mesuree.hyp --mode production --env mesure=5
hypomnesis lancer languages/mecanique --demande "Crée une plaque de 200 × 150 mm, masse maximale 1 kg."
hypomnesis lancer languages/ventilation programs/ventilation/salle_serveurs.hyp --mode production --env panne=1
```

Les procédures sont écrites en Hypomnesis : ce sont des valeurs `'a Effect.t` (observer, agir,
résoudre, enregistrer, retirer) que seul le moteur exécute, à travers contrats et permissions.
Exemple, extrait de `languages/mecanique/plaque.hyp` :

```ocaml
let concevoir (d : demande) (est : estimateur) =
  donnees d >>= fun () ->
  let estimation = est.estimer d in
  Effect.record "epaisseur.estimation" estimation est.id (Effect.Estimated est.confiance) >>= fun () ->
  Effect.solve (probleme d estimation) >>= fun solution -> …
``` Voir
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

## VS Code

L'extension [editors/vscode](editors/vscode/README.md) fournit la coloration `.hyp` et les
diagnostics du compilateur pendant la frappe, sans exécuter les programmes édités.
Installer `hypomnesis[lsp]` dans le Python du projet, puis construire et installer le VSIX :

```bash
pip install -e '.[lsp]'
cd editors/vscode
npm ci && npm test && npm run package
code --install-extension hypomnesis.vsix
```

La construction nécessite Node.js 22 ou supérieur. La coloration fonctionne sans Python ;
le linter utilise `.venv` par défaut, avec un contexte M2 automatique ou le réglage
`hypomnesis.languageRoot`.

## Inspecter les extensions

```bash
hypomnesis plugins list --manifest extensions/ --manifest autre-extension.json
hypomnesis plugins list --manifest extensions/ --role Solver
hypomnesis plugins show mon.extension --manifest extensions/ --version 1.0.0
```

`--manifest` est répétable : fichier JSON ou dossier dont seuls les `*.json` immédiats sont
lus. Sans chemin, le registre est vide ; aucune découverte implicite. La sortie est du JSON
indenté : `list` affiche toutes les versions, `show` le manifeste complet (version la plus récente
si `--version` est omis). Aucun backend n'est importé ou exécuté ; une dépendance absente
n'empêche pas l'inspection.

L'API `ExtensionRegistry` valide les manifestes, protège les métadonnées par copie et résout
explicitement les dépendances SemVer avec backtracking (`resolve({"mon.extension": ">=1.0.0,<2"})`).
Voir [TECHNICAL.md](TECHNICAL.md#registre-statique-des-extensions-hyp-041) pour l'API et les limites.
Le chargement effectif des backends reste hors de ce registre statique.

## Licence

Hypomnesis est distribué sous [licence MIT](LICENSE) : vous pouvez l'utiliser, le modifier et
le redistribuer, y compris dans un logiciel fermé, à condition de conserver la mention de
copyright et la licence. Les dépendances d'exécution (lark, jsonschema, referencing, z3-solver)
sont également sous licences permissives. Pour contribuer, voir [CONTRIBUTING.md](CONTRIBUTING.md).

Le dépôt ne contient pas de poids de modèles de langage : les modèles utilisés pour les bancs
d'essai restent soumis à leurs propres conditions.

## Développement

```bash
pytest                    # tests unitaires, propriétés (Hypothesis), contrats
ruff check . && ruff format --check .
pyright
```
