# Stratégie de vérification : une preuve tenue en parallèle du compilateur

## Principe : prouver le vérificateur, pas le compilateur

Prouver directement le compilateur Python (parser, inférence HM, élaborateur, interpréteur)
serait coûteux, et cette preuve serait cassée à chaque évolution. On adopte plutôt
l'approche du **compilateur certifiant**, ou validation de traduction, utilisée par exemple
pour certaines passes de CompCert et par les noyaux d'assistants de preuve :

```text
          source .hyp
              │
   ┌──────────▼───────────┐   non prouvé, libre d'évoluer
   │  compilateur Python  │   parser, inférence HM, élaboration
   └──────────┬───────────┘
              │ certificat = Core IR élaborée, annotée par ses types (JSON)
   ┌──────────▼───────────┐   PROUVÉ : typeOf_sound, typeOf_complete
   │ vérificateur Lean    │
   └──────────┬───────────┘
              │ accepté ⇒ (eval_safe) le programme ne peut pas se bloquer
   ┌──────────▼───────────┐
   │ runtime              │   Python aujourd'hui ; écart couvert par tests différentiels
   └──────────────────────┘
```

La base de confiance se réduit à la sémantique Lean, au vérificateur `typeOf` (prouvé) et au
noyau de Lean. L'inférence Python peut être fausse : au pire, elle produit un certificat
rejeté, jamais un programme mal typé accepté.

## Les trois liens à maintenir

| Lien | Garantie | Mécanisme |
|---|---|---|
| Python élaboré → Lean | le programme exécuté est celui qui a été vérifié | export du certificat, revérifié par `typeOf` |
| sémantique Lean ↔ interpréteur Python | l'interpréteur se comporte comme la sémantique prouvée | **tests différentiels** : Hypothesis génère des termes bien typés, que l'on exécute des deux côtés en comparant les résultats |
| Core IR Python ↔ `Syntax.lean` | les deux définitions décrivent le même langage | table de correspondance en tête de `Syntax.lean`, et la règle de discipline ci-dessous |

## Règle de discipline

Toute modification de la Core IR (`src/hypomnesis/ir/core.py`) ou de la sémantique de
l'interpréteur doit, **dans le même changement** :

1. mettre à jour `formal/Hypomnesis/Core/` (syntaxe, typage, évaluation) ;
2. réparer les preuves, ou marquer explicitement le nouveau constructeur comme hors du
   fragment prouvé dans `docs/verification/proprietes.md` ;
3. garder la CI verte : `lake build`, absence de `sorry`, audit des axiomes.

## Pont de certificats (lot F3) — étapes

1. ✅ **Annoter l'élaboration** (HYP-024). `Checker` enregistre le type de chaque paramètre de
   lambda, les quantificateurs de chaque `let` et les instanciations de schémas polymorphes.
2. ✅ **Exporter** (HYP-025). La Core IR est traduite en indices de de Bruijn et sérialisée en
   JSON, selon un schéma versionné (`contracts/schemas/certificate-1.1.0.json`, lecture 1.0 conservée), ce qui
   réutilise l'ADR 0004. CLI : `hypomnesis check --emit-certificate`.
3. ✅ **Vérifier** (HYP-026). L'exécutable Lean `hypomnesis-check` relit le certificat, le
   traduit dans le fragment et applique `typeOf`. Le décodeur (`formal/Hypomnesis/Certificate.lean`)
   n'est pas prouvé et n'a pas à l'être : il ne fait que construire des termes que `typeOf`
   vérifie, il peut faire rejeter un bon programme mais jamais en faire accepter un mauvais. Il
   monomorphise les définitions polymorphes atteignables et signale ce qui sort du fragment
   (code 2), notamment le polymorphisme local, les alias de motifs et la récursion
   mutuelle. Les scalaires binary64/Unicode, records et alternatives racines sont
   pris en charge ; voir [certification.md](certification.md) pour les limites exactes.
   Le même exécutable expose `eval` (sémantique de référence).
4. **Intégrer.** `hypomnesis check --certify` appelle le vérificateur, et la CI certifie tous
   les exemples.
5. **Tests différentiels (HYP-028).** `tests/differential/` génère par types des
   expressions fermées : entiers arbitraires, booléens, chaînes Unicode, tuples,
   listes, options et records ; conditions, portées locales, applications et
   récursion bornée. Les flottants sont observés par leurs comparaisons, pas par
   un arrondi de leur affichage décimal. Les autres cas binary64 sont couverts
   par les régressions de certification.

   Chaque source est élaborée une fois. Le certificat conserve toutes ses
   dépendances mais observe uniquement la dernière définition monomorphe
   `answer` (`program_start`) ; le même IR est exécuté par Python. Comparaison
   exacte des données structurées et des erreurs, dont `Match_failure` et
   `Division_by_zero`, jamais une recherche de sous-chaîne dans la sortie.

   Les pas Lean et Python ne sont pas assimilés : la génération est bornée,
   les deux évaluations doivent terminer, et un timeout Lean est un échec du
   test, pas une égalité. Une régression vérifie un budget insuffisant puis
   l'accord avec budget suffisant. Une autre mute une compilation de littéral
   Python et exige que le même comparateur détecte la divergence.

   Hypothesis exécute 500 exemples générés (plus les exemples explicites),
   avec statistiques visibles en CI. Le job des preuves et le validateur
   `lean`/`complet` construisent le checker puis exigent sa présence via
   `HYPOMNESIS_REQUIRE_LEAN=1`. Les jobs Python sans Lean peuvent ignorer
   ces tests, sans remplacer le job des preuves obligatoire.

## Ce qui reste de confiance

### Exhaustivité : preuve distincte du typage (HYP-022)

`Core.Coverage.exhaustive_sound` relie une analyse par matrices à la réussite
de `matchPat`. Budget explicite : `none` n'est jamais un verdict couvert.
`guarded_exhaustive_selects` ignore les bras gardés pour établir la couverture.
`Coverage.Certified` renforce ensuite le typage ordinaire par la certification
des groupes de filtrage et de toutes leurs sous-expressions/corps de fonctions.
Les environnements protégés conservent cette propriété dans les fermetures et
les appels récursifs. `certified_program_no_matchFail` porte sur le même
`Core.eval`, pour tout budget, et non sur un interpréteur simplifié.

La CLI ne construit pas encore ces dérivations. L'absence d'avertissement
Python n'est pas assimilée à la preuve renforcée. Les 31 cas ciblés et
240 matrices finies générées comparent le véritable checker Python à Lean ;
quatre tests vérifient les limites du budget. Le job Lean et les validateurs
`lean`/`complet` exigent leur exécution, sans substitution si Lean est absent.
Le pont de normalisation des alias/alternatives est testé, pas prouvé ;
aucune équivalence des alternatives gardées imbriquées n'est revendiquée.

### Base de confiance

- le noyau de Lean et les axiomes `propext`, `Quot.sound` et `Classical.choice`
  (modèle Float standard, audités en CI : ni `sorryAx`, ni
  axiome ajouté) ;
- la fidélité de l'interpréteur Python, couverte par les tests et non par une preuve, jusqu'à
  un éventuel runtime extrait de Lean ou le backend V1.0 ;
- l'adéquation des énoncés à l'intention du cahier des charges : c'est l'objet de la revue
  humaine de [proprietes.md](proprietes.md).

## Commandes

```bash
cd formal
lake build                                   # vérifie toutes les preuves
lake env lean Audit.lean                     # axiomes de chaque théorème principal
```

Depuis la racine, après construction du checker :

```bash
HYPOMNESIS_REQUIRE_LEAN=1 .venv/bin/python -m pytest tests/differential --hypothesis-show-statistics
```
