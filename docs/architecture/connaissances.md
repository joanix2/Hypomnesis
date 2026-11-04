# Connaissances immuables et échanges typés (HYP-030)

Le modèle de `src/hypomnesis/epistemics/knowledge.py` complète la base existante,
sans changer les signatures des opérations `observe`, `estimate` et `derive`.

## Identités et axes

- `Fact.key` identifie une propriété logique. Une révision conserve cette clé,
  pas nécessairement la même valeur ni la même provenance.
- `Source.id` identifie une source ; `Observation.id` est cet identifiant.
  Les échanges JSON préservent les identifiants sans en générer de nouveaux.
  Le compteur de `KnowledgeBase` reste local à la base : aucune unicité globale
  entre bases indépendantes n'est promise.
- `Observation(source, fact)` exige une source de genre `observation`, une
  provenance directe `obs(source.id)` et aucune prémisse.
- `Unknown(key, description)` est une métavariable non résolue, jamais une valeur
  concrète. Propositions, contraintes et résolution relèvent de HYP-032.

Suivant la spécification v0.3 §7.1, le support est calculé depuis la provenance :
`Observed`, `Estimated`, `Defaulted`, `Hypothesis`. `Derived` désigne la méthode
et les prémisses, pas un grade supplémentaire. Le type ou l'origine d'une
proposition ne prouve pas sa cohérence ; la détection des conflits reste HYP-035.
Une inconnue sans proposition n'a ni valeur ni provenance concrète inventée.

## Immuabilité

`Fact`, `Source`, `Unknown` et `Observation` sont gelés. Un fait capture
récursivement ses valeurs dans un arbre immuable interne. L'entrée peut contenir
des scalaires finis, des dictionnaires à clés chaînes, listes et tuples, ainsi
que les `RecordValue` et `Variant` du runtime.

`fact.value` reconstruit des conteneurs détachés : modifier le conteneur initial
ou celui retourné ne modifie pas le fait. Les types des scalaires, les conteneurs
et les constructeurs nominaux sont conservés. Les cycles, objets arbitraires,
fonctions et nombres non finis sont refusés explicitement (`ValueError`).
Construire un nouvel instantané avec `Fact(key, value, provenance, method, premises)`.
Les prémisses répétées restent autorisées : elles conservent le sens du produit
de provenance et de son évaluation, notamment de confiance.

Les genres de source, identifiants non vides et confiances dans `[0, 1]` sont
contrôlés avant enregistrement. Un échec de construction n'ajoute ni fait,
ni source, ni événement au journal. Un numéro local peut être consommé :
les identifiants ne promettent pas une séquence sans trous.
La base reste mutable ; HYP-030 ne prétend pas avoir rendu `KnowledgeBase`
persistante ou pure. Depuis HYP-033, `journal` expose un tuple en lecture
seule d'événements gelés, chacun pouvant conserver un instantané de fait.

## Provenance et révision (HYP-031, HYP-033)

Les quatre lectures sont `SUPPORT`, `BOOLEAN`, `CONFIDENCE` (Viterbi) et
`COST` (tropical) dans `epistemics.provenance`. Le coût utilise des nombres
non négatifs : `min` choisit une alternative, `+` additionne les prémisses,
`inf` signifie aucune dérivation et `0` une preuve sans prémisse.
La confiance flottante approxime le modèle exact, testé sur rationnels.
Les tests générés citent les énoncés Lean `eval_subst`, `holds_after_retract`,
`retract_unrelated` et `support_mono` ; ce sont des tests Python, pas une
preuve de correction du moteur Python.

`revision.dependency_index` construit l'index inverse observation → clés
depuis les provenances actuelles. L'index est reconstruit à la demande,
car les dictionnaires historiques de la base restent accessibles ; pas de
cache susceptible d'ignorer un fait ajouté par l'hôte. Seuls les faits qui
mentionnent une source retirée sont évalués pour décider l'invalidation.
`revision.recompute` est la référence exhaustive, comparée sur des bases
générées à plusieurs retraits successifs. Une dérivation alternative survit
si une source suffit encore ; support et confiance ignorent alors les sources
retirées. Les constantes `axiome` ne peuvent pas être rétractées.

`replace_observation` valide la nouvelle valeur avant tout changement, retire
la source précédente et enregistre la nouvelle observation. Les conclusions
invalidées deviennent des métavariables : la méthode d'un fait est un libellé,
pas du code à réexécuter implicitement. Le moteur de règles ou l'appelant doit
les dériver à nouveau. L'ancien `observe` conserve sa sémantique de remplacement
local, sans retrait implicite de l'ancienne source.

Le journal comporte notamment `observed`, `derived`, `replaced`, `retracted`,
`invalidated`, `revised`. Les anciens faits sont conservés dans les événements
de remplacement et d'invalidation. Ni le tuple retourné ni un événement
ne permettent d'effacer ou réécrire l'histoire par l'API publique.

## Contrat JSON

`epistemics.serialization.to_json(snapshot, codec)` et
`from_json(data, codec)` utilisent le contrat fermé
`https://schemas.example.org/hypomnesis/knowledge/1.0.0`.
Il distingue `fact`, `observation` et `unknown`, versionne les métadonnées,
et encode les cinq constructeurs de provenance (`obs`, `zero`, `one`, `plus`,
`times`) sans perdre les dérivations alternatives.

Le **type fermé attendu est fourni par l'hôte** via `TypeCodec`, à partir du
vérificateur du langage. Le document porte sa description structurée
`{name, args}` ; une différence est refusée. Le codec contrôle la valeur et
reconstruit records, variants, listes, tuples, unité et scalaires. Les types
ouverts, fonctions et autres types sans contrat sont refusés par `TypeCodec`.
Une inconnue a un type attendu mais aucun champ `value`.

Le schéma de connaissances contrôle les métadonnées, **pas à lui seul la valeur
du langage** : ne pas remplacer `from_json` par une simple validation de schéma.
Un champ supplémentaire, une version inconnue ou une provenance mal formée
produit `ContractError` ; un type ou une valeur incompatible produit `CodecError`.
Les invariants croisés d'observation sont vérifiés après le schéma.

```python
import json

from hypomnesis.contracts.codec import TypeCodec
from hypomnesis.epistemics.knowledge import KnowledgeBase, Observation
from hypomnesis.epistemics.serialization import from_json, to_json
from hypomnesis.session import Session

session = Session()
codec = TypeCodec(session.checker, "int")
base = KnowledgeBase()
fact = base.observe("objet.taille", 3, "capteur")
observation = Observation(base.sources[base.source_id(fact.key)], fact)
document = json.loads(json.dumps(to_json(observation, codec), allow_nan=False))
assert from_json(document, codec) == observation
```

Le décodage ne modifie aucune base et ne lance aucune règle ou extension.
La provenance seule ne contient pas les déclarations de toutes ses sources :
les faits dérivés nécessitent le contexte de sources de leur base pour évaluer
support et confiance. Ce format est un instantané typé, pas l'export complet
d'une base avec rejeu du journal (HYP-034). Les identités de types nominaux sont
interprétées dans l'environnement de types de l'hôte, pas authentifiées par
leur seul nom. Aucun certificat de conformité à une intention humaine ou
nouveau théorème Lean n'est établi par ce format.
