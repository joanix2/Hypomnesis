# Scénario de rétroaction bornée (HYP-068)

Le programme M1
[`salle_serveurs.hyp`](../../demo/programs/ventilation/salle_serveurs.hyp)
décrit une installation et appelle
`Ventilation.reguler_avec_confirmation installation "thermo-2"`.
Le DSL M2 porte intégralement seuil, décision de vitesse, critère de
confirmation et boucle. `reguler installation` reste compatible avec les
programmes utilisant le même capteur avant/après.

1. Une hypothèse explicite pose le fonctionnement du ventilateur.
2. `thermo-1` observe la température ; une règle pure décide la vitesse.
3. Le résultat attendu dépend de l'observation et de l'hypothèse : son
   support reste Hypothesis, même après une commande acceptée.
4. Le dispatcher contrôle contrats et permissions, puis exécute la commande.
5. Seulement après `Completed`, `thermo-2` fournit la mesure de confirmation.
6. Une baisse d'au moins 1 °C confirme **la baisse observée**. Sinon la
   source de l'hypothèse est retirée : les effets attendus dépendants
   sont invalidés, les observations et décisions restent au journal.

La réfutation observée n'est pas une preuve absolue de panne : capteurs,
environnement et causalité ont leurs propres limites. Dans cette démo,
les deux identifiants lisent la même pièce simulée ; ce ne sont pas deux
sources physiques indépendantes. Les relevés et échanges traversent les
contrats et transports HYP-063.

## Bornes et résultats honnêtes

`installation.budget` borne le nombre de commandes, indépendamment du
budget d'étapes du moteur. Zéro autorise la lecture initiale mais aucune
action ; un budget négatif est une erreur. La température absente ne
devient jamais silencieusement 0 °C. Le seuil atteint après la dernière
action autorisée est reconnu comme réussite, pas comme budget épuisé.

Dry-run, simulation, rejet, échec et issue inconnue arrêtent la boucle avec
`commande non confirmée : <état>`. Ils ne constituent pas une observation
de panne et ne rétractent pas l'hypothèse. Aucune commande automatique
supplémentaire n'est envoyée après une issue inconnue.

## Frontière pure / I/O

La trace expose :

- `language.typecheck` : chargement typé du programme ;
- `procedure.resume`, attribut `boundary=pure` : évaluation de la continuation
  Hypomnesis qui construit la prochaine valeur d'effet ;
- `observer.read` : appel du capteur et validation de son message ;
- `command.dispatch` : pipeline d'autorisation et sélection du mode ;
- `actuator.execute` : appel effectif de l'adaptateur, uniquement en production.

Les reprises pures sont sœurs des opérations I/O, jamais leurs parents.
Cette classification suppose que les natifs fournis par l'hôte respectent
leurs contrats ; le runtime Python n'est pas une sandbox.

```bash
python examples/robotics/feedback.py --sortie demo/sortie/feedback-ok
python examples/robotics/feedback.py --panne --sortie demo/sortie/feedback-panne
```

Le premier cas confirme la baisse et s'arrête sous le seuil. Le second
rétracte l'hypothèse après une seule commande. Chaque dossier conserve
rapport JSON, graphe de provenance, arbre de traces et transcript JSONL.
Le transcript se rejoue comme messages (pas comme actions physiques),
suivant [transports.md](transports.md).

Les tests comparent aussi la règle M2 au moteur générique HYP-050 :
`language_rule` utilise la même fonction `Ventilation.decider` via un
adaptateur `Json.t list -> Json.t option`, sans recopier la logique en Python.
