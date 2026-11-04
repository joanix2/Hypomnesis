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
`problem/1.0.0` : objets fermés, version obligatoire, et chaque nombre sous forme
`{"numerator": entier, "denominator": entier_positif}`. Le JSON préserve rationnels
et entiers arbitraires ; le schéma vérifie la forme, puis les constructeurs
vérifient les références et invariants sémantiques.

La rigidité linéarisée et la plage d'épaisseur du scénario mécanique se
représentent par une variable bornée et une contrainte linéaire.
`check_assignment` vérifie indépendamment du solveur domaines et contraintes ;
une solution proposée n'est pas considérée correcte sur la seule foi du plugin.
