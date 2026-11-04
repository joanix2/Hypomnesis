# Estimateur de régression optionnel (HYP-054)

Installer `pip install -e '.[sklearn]'`. Le noyau et ses imports n'exigent
ni NumPy, ni SciPy, ni scikit-learn ; le backend charge la bibliothèque
seulement à sa construction. La suite `tests/optional/` exige cet extra.
La CI core-only l'exclut et vérifie l'absence de ces bibliothèques ; la
validation complète et le job de tests complet l'exécutent sans skip.
Ce périmètre précise [ADR 0012](../adr/0012-codegen-separe-du-moteur.md) :
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
