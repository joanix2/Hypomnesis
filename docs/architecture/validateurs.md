# Validateurs et contre-exemples (HYP-055)

`engine.validators.LanguageValidator(session, function, input_type)` respecte
le protocole `Validator`. L'hôte choisit une fonction Hypomnesis pure, de type
fermé `input_type -> string list`. Une liste vide signifie acceptation ;
chaque message non vide désigne une violation. Le moteur ne connaît aucune
règle géométrique.

L'entrée est une valeur runtime nominale, vérifiée et capturée par un TypeCodec
fermé. Une acceptation rend la valeur vérifiée et un
`Certificate("validator.accepted", ...)` contenant :

- nom du vérificateur de confiance et type d'entrée ;
- proposition complète en JSON typé ;
- liste vide de violations.

Un rejet logique (`validator.rejected`) ne rend aucune valeur acceptée. Son
diagnostic contient `data["counterexample"]` : la même enveloppe avec les
violations effectivement obtenues. Il n'existe pas de rejet logique sans ce
témoin complet. Le certificat ne choisit jamais le code à exécuter.

`recheck(evidence)` utilise exclusivement le vérificateur configuré par l'hôte,
redécode l'entrée et recalcule les violations. Un rejeu valide a `ok=True` :
sa valeur est True pour une proposition acceptée, False pour un contre-exemple
confirmé. Une enveloppe inconnue, un type incorrect, un autre nom de fonction
ou des violations falsifiées donnent un diagnostic `validator.evidence`.

Ces témoins sont computationnels et relatifs au vérificateur M2 de confiance
chargé par l'hôte : pas des preuves Lean, ni une signature authentifiant le
programme ou l'origine de la proposition. Une nouvelle session avec le même
DSL peut les rejouer sans utiliser l'instance qui a produit le rejet.
Valider ne crée aucun fait Observed et ne promeut aucune estimation.

## Erreurs et réfutations sont distinctes

Une entrée ne satisfaisant pas le TypeCodec produit `validator.input`.
Une erreur d'évaluation du vérificateur produit `validator.checker`.
Ce sont des échecs opérationnels, **pas** des rejets mathématiques : aucun
contre-exemple logique n'est inventé dans ces cas. Les erreurs remontent dans
Result avec leur phase ; aucune acceptation de secours n'est fournie.
La pureté des natifs fournis par l'hôte reste une frontière de confiance ;
Python n'est pas sandboxé.

## Géométrie du scénario M2

`Plaque.proposition = { demande; epaisseur_proposee }` et
`Plaque.verifier_proposition` adaptent le vérificateur géométrique existant.
L'hôte utilise :

```python
validator = LanguageValidator(language.session, "Plaque.verifier_proposition", "Plaque.proposition")
result = validator.validate(proposition)
```

Le DSL vérifie dimensions et masse maximale positives, épaisseur minimale,
élancement et masse. Une épaisseur nulle est rejetée sans division par zéro.
Les tests rejouent chaque rejet dans une session indépendante et contrôlent
la falsification du témoin. Il s'agit de la géométrie/règle simplifiée du
scénario, pas d'une certification de résistance mécanique.
