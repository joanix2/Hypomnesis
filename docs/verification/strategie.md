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

1. **Annoter l'élaboration.** `Checker` enregistre le type de chaque paramètre de lambda et
   les instanciations de schémas polymorphes, qu'il calcule déjà.
2. **Exporter.** Traduire la Core IR en indices de de Bruijn et la sérialiser en JSON, selon
   un schéma versionné (`contracts/schemas/certificate-1.0.0.json`), ce qui réutilise
   l'ADR 0004.
3. **Vérifier.** Un exécutable Lean `hypomnesis-check` (via `lake exe`, avec `Lean.Json`)
   relit le certificat et applique `typeOf`.
4. **Intégrer.** `hypomnesis check --certify` appelle le vérificateur, et la CI certifie tous
   les exemples.
5. **Tests différentiels.** Le même exécutable expose `eval`, et un test Hypothesis compare
   ses résultats à l'interpréteur Python.

## Ce qui reste de confiance

- le noyau de Lean et les axiomes `propext` et `Quot.sound` (audités en CI : ni `sorryAx`, ni
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
