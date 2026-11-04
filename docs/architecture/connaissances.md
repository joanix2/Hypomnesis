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
  concrète. `MetaVar` (HYP-032, ci-dessous) complète ce marqueur par les
  propositions typées, contraintes et résolution persistante.

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

## Métavariables et propositions (HYP-032)

`epistemics.metavariables.MetaVar(id, codec, constraints=())` représente
un trou typé. Son `TypeCodec` fermé vient de l'hôte ; la propriété `type`
expose ce type sans créer un second système de typage. Cette API Python
n'ajoute ni sentinelle au runtime ni nouvelle forme de Core IR.

Les trois axes restent séparés :

- `state` vaut `unresolved`, `proposed` ou `resolved`.
- `grade` est le support de la proposition sélectionnée, ou `None` avant
  résolution. `proposals` conserve chaque instantané Fact, support et provenance.
- `coherence` vaut `consistent` ou `conflict`. Ici un conflit signifie des
  valeurs typées inégales pour le même trou ; ce n'est pas encore le détecteur
  logique général HYP-035 ni une théorie d'égalité propre à un domaine.

`Constraint(name, accepts)` impose un prédicat pur fourni par l'hôte,
retournant exactement `True` pour une valeur admissible. Les noms sont
distincts. Type et contraintes sont vérifiés avant acceptation d'une proposition.
Les erreurs de prédicat sont remontées ; aucun état existant n'est modifié.
Les opérations suivantes retournent un nouvel état :

- `propose(meta, value, grade, provenance)` ajoute une proposition et rouvre
  la résolution, même si `meta` était résolue.
- `best(meta)` choisit le meilleur support. Des valeurs incompatibles au même
  meilleur grade produisent `ResolutionConflict`, jamais un gagnant arbitraire.
- `conflict(meta)` reste vrai si **n'importe quelles** propositions diffèrent,
  même si une observation a un meilleur support qu'une estimation.
- `resolve(meta)` sélectionne la meilleure proposition si elles sont cohérentes.
  En présence de conflit, un `choice=<index>` explicite est requis. Ce choix
  ne supprime ni les autres propositions ni le constat de conflit.

Lire `meta.value` sans résolution lève `UnresolvedMetaVar`. Une métavariable
ne peut pas être stockée directement comme valeur d'un Fact, même résolue :
l'appelant doit demander explicitement sa valeur. Les propositions vides,
mauvais types, contraintes violées, grades non typés ou Unsupported et indices
invalides sont refusés sans valeur de secours.

```python
from hypomnesis.epistemics.metavariables import MetaVar, best, conflict, propose, resolve
from hypomnesis.epistemics.provenance import Support, obs

hole = MetaVar("demande.epaisseur", codec)  # codec int de l'exemple ci-dessus
estimated = propose(hole, 3, Support.ESTIMATED, obs("estimateur"))
measured = propose(estimated, 4, Support.OBSERVED, obs("capteur"))
assert best(measured).grade == Support.OBSERVED
assert conflict(measured)
chosen = resolve(measured, choice=1)  # décision explicite de l'hôte
assert chosen.value == 4 and chosen.coherence == "conflict"
assert hole.state == "unresolved" and estimated.state == "proposed"
```

Le grade d'une **proposition** est un jugement fourni par l'hôte, pas une
preuve reconstruite à partir d'un identifiant de source inconnu. Pour une
proposition issue d'une base existante, passer `base.support(key)` et
`base.facts[key].provenance` ; les dérivations de la base continuent à calculer
leur support depuis les sources, sans accepter ce grade comme une promotion.
Une future sortie LLM doit être estampillée Hypothesis à sa frontière de
confiance, jamais autorisée à se déclarer Observed elle-même (HYP-082).
Ni ces propositions ni leur résolution ne changent automatiquement une
KnowledgeBase ou son journal ; l'intégration des stratégies revient aux capacités.

## Chaînage avant et défauts (HYP-050)

`engine.rules.Rule(name, target, premises, evaluate, default=False)` décrit
une règle pure à prémisses explicites. Le callback reçoit un tuple de valeurs
détachées, retourne `Conclusion(value)` ou `None` si sa condition ne s'applique
pas. `Conclusion(None)` conclut réellement la valeur nulle. Il ne doit lire
aucun état externe ni lancer d'effet ; le moteur ne sandboxe pas Python.

`RuleEngine(base, rules).run(budget=1000)` publie les conclusions dans la
base et recommence jusqu'à un passage complet sans changement. Chaque règle
visitée consomme une unité, même avec prémisses absentes. Le rapport contient
`evaluations`, `published` et un statut `fixed_point` ou `budget_exhausted`.
Atteindre exactement la limite après une publication ne prouve pas le point
fixe : il faut encore vérifier l'absence de changement. Un budget nul
n'évalue aucune règle ; un ensemble vide est déjà au point fixe.

Les prémisses multiplient leurs provenances, répétitions comprises. Les
contributions concordantes des règles sont additionnées une fois chacune,
dans l'ordre de leurs noms ; un nouveau passage au point fixe ne réécrit
pas le journal. Des valeurs incompatibles produisent `RuleConflict`,
avec la cible et les faits concurrents, sans gagnant arbitraire. Les types
scalaires restent distincts (`True` n'est pas `1`) et l'ordre des clés
d'objets n'introduit pas de conflit. Ce contrôle n'est pas HYP-035.

Un défaut ajoute sa propre source Defaulted révocable. Une observation
remplaçant directement sa cible retire cette source lors du prochain
`run`, invalide ses dépendants et permet leur recalcul. Observer une
conclusion en aval ne retire pas les défauts de ses prémisses. Un défaut
ne remplace jamais un fait externe. Une règle ordinaire sans prémisse
reste une constante Defaulted sur `axiome`, non une observation.
Les modifications d'observations utilisent `replace_observation`.

Le moteur est positif, sans négation par absence. Les conclusions d'un
passage sont publiées progressivement : un conflit ou une erreur de
callback interrompt l'exécution mais n'annule pas les publications déjà
validées. Chaque publication individuelle valide ses sources et prémisses
avant modification. La récursion peut faire croître la provenance libre
sans fin même avec une valeur stable ; le budget reste alors la limite,
sans faux signal de point fixe. Réutiliser la même instance conserve
les contributions et la gestion des défauts ; ce n'est pas un état durable.

`language_rule(session, name, target, premises, function)` adapte une fonction
Hypomnesis monomorphe `Json.t list -> Json.t option`, sans nouveau natif
ni forme Core IR. Le DSL porte la logique métier ; Python fournit seulement
les entrées et le chaînage générique. Exemple exécutable :
`python examples/knowledge/rules.py`, utilisant
[`regles.hyp`](../../demo/examples/knowledge/regles.hyp).

## Bibliothèque pure du langage (HYP-038)

Le prélude expose `Knowledge` sans nouveau natif ni effet : types algébriques,
records immuables et fonctions Hypomnesis ordinaires, utilisant uniquement
les primitives du registre fermé déjà présent. Une base `'a Knowledge.t`
est passée explicitement à chaque fonction ; aucune base globale n'est lue.

| API | Résultat |
|---|---|
| `empty ()` | base vide persistante |
| `lookup base key` | `'a fact option`, valeur et justification |
| `value base key` | `'a option`, absence explicite sans sentinelle |
| `known base key` | présence d'une valeur, indépendante de son support |
| `support base key` | grade calculé depuis la provenance et les sources |
| `provenance base key` | terme libre Source/Zero/One/Plus/Times |
| `derive base key value method premises` | nouvelle base avec la conclusion et ses prémisses |

Une dérivation multiplie les provenances des prémisses, y compris les
répétitions. Une dérivation sans prémisse repose sur `axiome`, Defaulted,
comme dans KnowledgeBase ; une source axiome incompatible ou retirée est
refusée. Les alternatives prennent le meilleur support, les prémisses
jointes le plus faible ; une source retirée vaut Unsupported.
Clé absente dans `support`, source inconnue ou prémisse absente dans `derive`
produisent une erreur explicite. `value` reste optionnelle.

L'existence n'est pas confondue avec le support : une valeur explicitement
présente dont la provenance vaut Zero est connue mais Unsupported.
Une révision normale de KnowledgeBase retire les faits invalidés ; son
instantané expose alors None pour ces clés. Cette bibliothèque ne lance
pas elle-même la révision, ne modifie aucun journal et ne conclut pas
automatiquement à l'absence de conflit logique (HYP-035).

`epistemics.language.snapshot_value(base, encode=...)` est le pont hôte vers
une vue `Json.t Knowledge.t`. Il capture les sources, faits, provenances et
retraits dans des valeurs runtime immuables. Par défaut, les valeurs doivent
être des données JSON strictes ; un fait nominal exige son encodeur explicite,
par exemple `encode=lambda fact: codec.encode(fact.value)`. Aucun type
nominal attendu n'est deviné depuis une charge non fiable.

L'hôte peut fournir cet instantané à un programme par un symbole déclaré
dans son propre registre, suivant ADR 0003 :

```python
from hypomnesis.epistemics.language import snapshot_value
from hypomnesis.runtime.natives import default_registry

view = snapshot_value(base)
registry = default_registry()
registry.register("app.context", 0, lambda: view)
session = Session(registry)
session.load('external context : Json.t Knowledge.t = "app.context"')
session.load("""
let result = Knowledge.derive context "conclusion" (Json.Bool true)
  "regle du programme" ["objet.taille"]
let grade = Knowledge.support result "conclusion"
""")
```

Le symbole d'application n'est pas ajouté au registre par défaut. Les vues
Knowledge sont des **données**, pas des attestations d'observation : un
programme peut construire des exemples fictifs, sans créer d'observation
dans la KnowledgeBase de l'hôte. Seul Effect.Observe conserve ce rôle dans
les procédures ; enregistrer un résultat avec Effect.Record suit toujours
ses contrôles et les prémisses de la base réelle. La provenance seule
ne prouve pas que le calcul de la valeur dérivée exprime correctement
une règle métier.

Exemple autonome :
[plaque.hyp](../../demo/examples/knowledge/plaque.hyp). Le calcul de surface
prend une base en argument, produit un fait automatiquement Estimated et
laisse l'entrée inchangée. Les tests générés comparent la lecture du support
à l'implémentation Python pour produits, alternatives et retraits.
Cette bibliothèque n'étend pas le fragment Lean prouvé : les tests Python
et différentiels ne sont pas une preuve de raffinement.
La provenance seule ne contient pas les déclarations de toutes ses sources :
les faits dérivés nécessitent le contexte de sources de leur base pour évaluer
support et confiance. Ce format est un instantané typé, pas l'export complet
d'une base avec rejeu du journal (HYP-034). Les identités de types nominaux sont
interprétées dans l'environnement de types de l'hôte, pas authentifiées par
leur seul nom. Aucun certificat de conformité à une intention humaine ou
nouveau théorème Lean n'est établi par ce format.
