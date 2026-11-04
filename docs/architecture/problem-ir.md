# Problem IR

La représentation indépendante du solveur est `hypomnesis.ir.problem.Problem`.
Ses variables définissent des bornes et/ou un domaine discret ; les contraintes
sont linéaires (`<=`, `>=`, `==`). L'objectif `target` minimise la distance
d'une variable à une valeur. Les autres formes d'objectif ne sont pas prises
en charge : il ne s'agit pas encore d'une algèbre générale d'optimisation.

Les structures immuables valident les identifiants, références, domaines et
nombres finis. Les valeurs sont normalisées en rationnels exacts ; les
flottants Python sont interprétés selon leur écriture décimale.

`State`, `Action` et `Transition` décrivent valeurs, préconditions, effets et
liaisons entre états. Aucune action n'est exécutée, aucun chemin n'est recherché.
Un solveur numérique existant ne résout que la partie variables/contraintes :
les transitions sont des données de planification, pas une preuve d'exécutabilité.

Dans le langage, `Problem.problem` conserve son format historique.
`Problem.planning_problem` l'enveloppe avec `states`, `actions`, `transitions`.
`engine.bridge.to_problem` accepte les deux et valide la structure obtenue.
Cela préserve les procédures et le backend Z3 existants.

`problem.to_json()` et `Problem.from_json(document)` utilisent le contrat
`problem/1.1.0` : objets fermés, version obligatoire, domaines `real`, `int`,
`bool` et chaque nombre sous forme
`{"numerator": entier, "denominator": entier_positif}`. Le JSON préserve rationnels
et entiers arbitraires ; le schéma vérifie la forme, puis les constructeurs
vérifient les références et invariants sémantiques.
Les booléens restent des booléens JSON, pas les entiers 0/1. La version 1.0
reste lisible et ses variables sont réelles ; sa définition n'est pas modifiée.

La rigidité linéarisée et la plage d'épaisseur du scénario mécanique se
représentent par une variable bornée et une contrainte linéaire.
`check_assignment` vérifie indépendamment du solveur domaines et contraintes ;
une solution proposée n'est pas considérée correcte sur la seule foi du plugin.

## Domaines typés et Z3 (HYP-052)

`Variable(..., kind="real"|"int"|"bool")` distingue les domaines. Le défaut
`real` préserve les anciens appels. Bornes et choix entiers doivent être
intégraux. Les booléens n'ont pas de bornes numériques ; leurs éventuels choix
sont de vrais booléens. Dans une contrainte linéaire seulement, une variable
booléenne vaut explicitement faux=0/vrai=1 (`If` Z3). Aucun booléen ne devient
un entier dans le modèle retourné ; ce n'est pas une algèbre générale de
formules booléennes.

`z3_solver.solve(problem, timeout_ms=1000)` crée les sortes Z3 correspondantes.
Il retourne `sat`, `unsat` ou `unknown`, la durée en millisecondes et une
raison pour `unknown`. Le délai positif est transmis à Z3 ; ce n'est pas une
borne de temps sur la traduction Python d'une entrée arbitrairement grande.
Les affectations sat sont Fraction/int/bool, contrôlées par évaluation
indépendante des contraintes. L'objectif emploie une variable fraîche.
Une réponse unsat est le verdict du backend, pas une preuve d'insatisfiabilité
rejouée par Lean. Le contrôle garantit la faisabilité du modèle, pas
l'optimalité annoncée par le solveur.

`Problem.typed_problem = { numeric; sorts }` enrichit le record historique :
la liste des sortes couvre exactement les variables, sans doublons. Les
champs numériques d'entrée restent ceux de `Problem.problem` ; un domaine
booléen s'y décrit sans bornes, avec choix vides ou 0.0/1.0. Le pont les
convertit explicitement et refuse toute autre valeur. Cette API ne transforme
pas les anciens champs float d'entrée en entiers arbitraires ; le JSON et
l'API Python conservent leurs rationnels exacts.

`Effect.solve_typed` renvoie un `Problem.solution` nominal :

- `verdict` : `Problem.Sat`, `Unsat` ou `Unknown` ;
- `assignment` : liste de paires nom/scalaire, avec `Rational (n, d)`,
  `IntegerValue i` ou `BooleanValue b` ;
- `duration_ms` et `reason : string option`.

Le pont revérifie le certificat avant restitution, indépendamment du champ
`violations` que pourrait annoncer un plugin. Aucun résultat n'est observé
ou enregistré automatiquement. Exemple exécutable sans effet matériel :

```bash
hypomnesis lancer demo/languages/solveur demo/programs/solveur/domaines.hyp
```

Le modèle contient l'entier 2, le réel exact 1/3 et le booléen true.
`Effect.solve` conserve son ancien résultat optionnel de floats pour les
DSL existants : cette projection historique peut arrondir un rationnel et
ne distingue pas unsat/unknown. Utiliser l'API typée pour conserver le
modèle exact et les statuts. Aucun nouveau natif ni forme Core IR ; seules
des données algébriques du prélude et leur interprétation d'effets sont ajoutées.
