# Estimateur de régression optionnel (HYP-054)

Installer `pip install -e '.[sklearn]'`. Le noyau et ses imports n'exigent
ni NumPy, ni SciPy, ni scikit-learn ; le backend charge la bibliothèque
seulement à sa construction. La suite `tests/optional/` exige cet extra.
La CI core-only l'exclut et vérifie l'absence de ces bibliothèques ; la
validation complète et le job de tests complet l'exécutent sans skip.
Ce périmètre est consigné pour revue dans
[ADR 0014](../adr/0014-backend-scientifique-optionnel.md), sans modifier
le texte accepté de l'ADR 0012 :
l'extra n'appartient ni à `dev` ni aux dépendances de base.

## Backend générique

`backends.sklearn.RegressionEstimator` reçoit `model`, `version`, les noms
de `features`, des lignes `training` et des lignes `validation`. Une ligne
contient les valeurs des caractéristiques suivies de la cible. Configuration
incorrecte, données non finies, validation vide, chevauchement des entrées
d'entraînement/validation ou caractéristique constante sont refusés.

L'algorithme est `sklearn.linear_model.LinearRegression`, déterministe,
sans chargement de pickle/joblib ni téléchargement de modèle. L'erreur
rapportée est la racine de l'erreur quadratique moyenne sur la validation
distincte. Les entrées de validation doivent être dans la boîte des bornes
d'entraînement. Cette boîte n'est pas une garantie de couverture conjointe
des caractéristiques.

`estimate({feature: value, ...})` respecte `Estimator` et rend
`Result[Prediction]`. Les clés doivent correspondre exactement au modèle ;
booléens, chaînes, NaN, infinis et extrapolation sont refusés avec diagnostics.
Une réussite fournit valeur, modèle, version et `validation_rmse`, également
présents dans le certificat descriptif. Ce certificat n'est pas une preuve Lean.

`Prediction.origin` conserve modèle/version/incertitude dans la source lorsque
l'hôte appelle explicitement `KnowledgeBase.estimate`. Ce choix garantit
Estimated, jamais Observed. La confiance scalaire de la source est un jugement
de l'hôte, distinct de la RMSE, pas une conversion arbitraire en probabilité.
La proposition d'une MetaVar reste non résolue jusqu'à décision explicite.
L'estimateur ne modifie ni base de connaissances ni métavariable.

## Jeu synthétique de démonstration

[`epaisseur-1.0.0.json`](../../demo/languages/mecanique/modeles/epaisseur-1.0.0.json)
est le modèle `plaque-epaisseur-synthetique`, version `1.0.0`. Sa caractéristique
`petit_cote_mm` et sa cible sont en mm. Les huit entrées d'entraînement sont
25, 50, 75, 100, 150, 200, 250 et 300 mm. Leurs cibles sont `x / 25` avec
une perturbation alternée de +0,1 puis -0,1 mm. Les quatre entrées de
validation 40, 80, 125 et 225 mm suivent exactement `x / 25`.

Cette construction synthétique est entièrement documentée, sans tirage
aléatoire ni donnée réelle. Le choix du petit côté relève du DSL M2
(`Plaque.petit_cote`), pas du backend. Le jeu n'est ni une mesure physique,
ni une étude de résistance, ni une recommandation pour dimensionner une pièce.
La RMSE empirique n'est pas une borne garantie, une variance prédictive
ou un intervalle de confiance calibré ; sa petite valeur sur ces quatre
points ne prouve rien hors de ce jeu artificiel.

```bash
python examples/knowledge/estimate.py
pytest tests/optional/test_sklearn_estimator.py
```

Le premier exemple fournit une entrée déjà calculée par le domaine et
propose une épaisseur typée float avec support Estimated, modèle/version
et RMSE dans la provenance, sans résoudre le trou. La validation géométrique
et les contraintes du scénario restent indépendantes de cette proposition.

## Substitution contractuelle sans modifier le M1 (HYP-045)

Le programme [plaque_plugins.hyp](../../demo/programs/mecanique/plaque_plugins.hyp)
appelle toujours `thickness.estimate : Plaque.demande -> float`. L'hôte
[substitution.py](../../examples/mechanics/substitution.py) choisit seulement
le manifeste : règle ou régression, même signature et mêmes schémas issus
du TypeCodec. Les deux utilisent le PythonBackend HYP-044, avec validation
avant/après appel, sous-processus récolté et délai effectif de 30 secondes.
La règle appelle `Plaque.estimer_regle` en M2 ; les caractéristiques de la
régression viennent de `Plaque.petit_cote`, sans formule métier recopiée en Python.

Depuis la racine :

```bash
python -m examples.mechanics.substitution demo/languages/mecanique/plugins/epaisseur-regle-1.0.0.json
python -m examples.mechanics.substitution demo/languages/mecanique/plugins/epaisseur-regression-1.0.0.json
```

Le second exige l'extra `sklearn`. La préparation et le typage n'importent
aucun fournisseur ; il n'est chargé qu'au premier appel réel. Les commandes
d'export restent en dry-run par défaut (`--mode simulate` les simule,
`--mode production --out CHEMIN` autorise les écritures locales de la démo).
Le JSON stdout inclut programme inchangé, manifeste sélectionné, provenance
et trace réelle du backend. Aucun modèle distant ni Codegen n'est nécessaire.

Pour le cas 120 × 80 mm, la règle propose 3,2 mm, la régression une valeur
proche mais distincte ; le même solveur Z3 retient 3 mm dans les deux
exécutions et le même validateur M2 accepte la pièce.
Une extrapolation du modèle est une erreur
explicite, jamais un retour silencieux à la règle.

Cette interface scalaire conserve le fournisseur/version dans la provenance.
Elle n'exporte pas le certificat descriptif complet du modèle : celui-ci reste
disponible via `RegressionEstimator` décrit plus haut et ses données versionnées.
Le support est Estimated, non Observed ; la confiance 0,6 est un choix
illustratif explicite du programme, pas une probabilité tirée de la RMSE.
Les données restent synthétiques, sans garantie physique.

Tests d'intégration règle/statique sans extra :
`pytest tests/integration/test_estimator_substitution.py`.
Les deux fournisseurs réels et le refus d'extrapolation :
`pytest tests/optional/test_estimator_substitution.py`.
