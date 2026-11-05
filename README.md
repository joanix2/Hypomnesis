# Hypomnesis

*A language for programmable knowledge and reasoning.*

Hypomnesis est un métalangage fonctionnel à syntaxe OCaml destiné à définir des DSL métiers :
concepts, connaissances, règles, contraintes, et capacités d'action contrôlées. Il ne remplace
ni les solveurs, ni les bibliothèques scientifiques : il fournit un langage typé pour les
décrire, les composer et contrôler leurs interactions.

- Spécification : [docs/specification/cahier-des-charges-v0.3.md](docs/specification/cahier-des-charges-v0.3.md)
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
| M2 | `demo/languages/` | des langages métier écrits en Hypomnesis : `mecanique`, `ventilation` |
| M1 | `demo/programs/` | des programmes écrits dans ces langages |
| M0 | `demo/sortie/` | les résultats : rapports, fichiers exportés |

La génération de programmes par LLM est un paquet optionnel séparé :
[`hypomnesis-codegen`](packages/codegen/README.md), sous `packages/codegen/`.
Le compilateur, le métalangage, le LSP et le moteur symbolique n'en dépendent pas.

```bash
hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_120x80.hyp
hypomnesis lancer demo/languages/mecanique demo/programs/mecanique/plaque_mesuree.hyp --mode production --env mesure=5
hypomnesis lancer demo/languages/mecanique --demande "Crée une plaque de 200 × 150 mm, masse maximale 1 kg."
hypomnesis lancer demo/languages/ventilation demo/programs/ventilation/salle_serveurs.hyp --mode production --env panne=1
```

Les procédures sont écrites en Hypomnesis : ce sont des valeurs `'a Effect.t` (observer, agir,
résoudre, enregistrer, retirer) que seul le moteur exécute, à travers contrats et permissions.
Exemple, extrait de `demo/languages/mecanique/plaque.hyp` :

```ocaml
let concevoir (d : demande) (est : estimateur) =
  donnees d >>= fun () ->
  let estimation = est.estimer d in
  Effect.record "epaisseur.estimation" estimation est.id (Effect.Estimated est.confiance) >>= fun () ->
  Effect.solve (probleme d estimation) >>= fun solution -> …
``` Voir
[ADR 0008](docs/adr/0008-niveaux-m3-m2-m1-m0.md).

## Couches de langages réutilisables

Chaque langage se déclare directement en `.hyp`, par convention dans `langage.hyp` :

```ocaml
language exemple = struct
  let version = "1.0.0"
  let imports = ["../booleen"; "../arithmetique"]
  let procedure = { kind = "program"; entry = "procedure" }
end
```

Les modules importés conservent leurs types et noms qualifiés (`Booleen.*`,
`Arithmetique.*`). Imports transitifs et diamants sont partagés ; cycles et collisions
sont refusés. Une couche bibliothèque n'a pas besoin de `procedure`.

```bash
hypomnesis layers demo/languages/composition_a
hypomnesis check demo/languages/composition_a/langage.hyp demo/programs/composition_a/exemple.hyp
```

Les anciens `langage.json` ne sont plus lus. Les entrées/sorties externes sont définies
par décorateurs Python (`@sensor`, `@actuator`, `@environment`, `@transcriber`) dans les
modules explicitement listés par `adapters`. Aucun module d'adaptateur n'est importé
pendant `check` ou l'analyse VS Code. Voir [la référence](docs/language/reference.md#couches-de-langages-et-imports)
et [l'ADR 0013](docs/adr/0013-couches-declarees-en-hypomnesis.md).
La syntaxe extérieure à accolades est remplacée sans compatibilité par
`struct / let / end` ([ADR 0016](docs/adr/0016-declarations-language-struct.md)).

## Démarrage

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'

hypomnesis run demo/examples/basics/tour.hyp
hypomnesis run demo/examples/mechanics/plate.hyp
hypomnesis check demo/examples/mechanics/plate.hyp
hypomnesis repl
```

Les fichiers déclarent leurs dépendances avec une syntaxe d'import Python :
`import units`, `from units import Length`, ou `from units import mm as millimetres`.
Le reste du langage conserve sa syntaxe fonctionnelle. Résolution locale relative
au fichier, cycles refusés, imports partagés ; `open` ne charge pas de fichier.

Le backend de régression est optionnel : `pip install -e '.[sklearn]'`.
La suite complète de développement demande `pip install -e '.[dev,sklearn]'`
et le paquet Codegen ; les tests du noyau seul se lancent avec
`pytest tests --ignore=tests/optional`, sans scikit-learn ni Codegen.
Exemple : `python examples/knowledge/estimate.py`.
Voir [l'estimateur synthétique](docs/architecture/estimateurs.md).

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

## Génération de programmes et LLM (optionnel)

```bash
pip install -e . -e packages/codegen
hypomnesis-codegen decrire demo/languages/ventilation
```

Le paquet regroupe traduction langage naturel → programme M1, prompts, recherche
d'exemples, client Ollama, bancs d'essai et graphiques. Ses commandes `decrire`,
`benchmark-llm` et `graphiques-llm` ne sont plus dans la CLI `hypomnesis`.
Les imports deviennent `hypomnesis_codegen.*` au lieu de `hypomnesis.llm.*`.
Les solveurs, validateurs et transpileurs symboliques ne relèvent pas de ce paquet.
Voir [l'ADR 0012](docs/adr/0012-codegen-separe-du-moteur.md).

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
pip install -e packages/codegen  # optionnel : tests des outils LLM sans modèle
pytest packages/codegen/tests
ruff check . && ruff format --check .
pyright
pyright --project packages/codegen  # si Codegen est installé
```

`pytest` seul teste le moteur, sans installer Codegen. La validation globale
`./scripts/validate.sh complet` couvre les deux distributions et exige leur installation.
