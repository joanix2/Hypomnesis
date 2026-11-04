# ADR 0010 — Types statiques, JSON Schema et encodage réversible

- **Statut :** acceptée
- **Contexte :** HYP-042, choix confirmés par l'utilisateur le 2026-11-04.
- **Références :** ADR 0003, ADR 0004, §6.1 et §13.4 du cahier des charges.

## Problème

Les contrats et les signatures doivent être cohérents avant tout appel d'extension.
Le pont historique effaçait `Some`/`None` : `None`, `Some ()` et `Some None` se confondaient.
Son passage par `Json.Num of float` arrondissait aussi les grands entiers. Un codec séparé
sans migration de ces ponts laisserait deux formats contradictoires.

## Décision : une représentation structurelle unique

| Type Hypomnesis | JSON / schéma Draft 2020-12 |
|---|---|
| `int` | entier JSON / `integer`, sans restriction à 53 bits |
| `float` | nombre fini / `number`, borné à ±`sys.float_info.max` |
| `string`, `bool` | `string`, `boolean` |
| `unit` | `null` |
| tuple | tableau de longueur exacte, `prefixItems`, `items: false` |
| liste | tableau homogène |
| record | objet fermé ; tous les champs sont requis |
| constructeur nullaire | objet fermé `{"tag": "Nom"}` |
| constructeur avec argument | objet fermé `{"tag": "Nom", "arg": ...}` |

Les options suivent les variants : `None` → `{"tag":"None"}`, `Some ()` →
`{"tag":"Some","arg":null}`, `Some None` → `{"tag":"Some","arg":{"tag":"None"}}`.
Les noms de constructeurs sont ceux des déclarations ; le type attendu fournit leur
propriétaire nominal et leur indice. Les records sont reconstruits dans l'ordre déclaré.

Les alias sont développés avec le compilateur existant ; les paramètres doivent être
instanciés par des types clos. Les types déclarés récursifs réguliers utilisent des
`$defs`/`$ref` locaux déterministes. Les types ouverts, inconnus, fonctionnels et les
récursions non régulières sont refusés explicitement. Les fonctions ne deviennent jamais
des chaînes ou des objets JSON de remplacement.

`bool` n'est pas un `int`. Le décodage de `integer` suit la définition mathématique de
JSON Schema : le token `1.0` est accepté et reconstruit comme l'entier `1`, sans troncature.
`float` accepte un nombre fini décodable ; NaN, infinis et dépassements sont refusés.
La garantie d'aller-retour porte sur les valeurs typées encodées, pas sur la conservation
du texte original d'un document JSON arbitraire.

## API et préparation statique

`TypeCodec(checker, signature_ou_type)` expose `schema`, `encode` et `decode`.
Il photographie les déclarations, ne modifie pas l'environnement d'inférence et rend
une copie du schéma. Les erreurs incluent un chemin JSON. La grammaire des signatures et
la résolution des noms sont celles des annotations du langage (`parse_type`,
`Checker.resolve_type`) : pas de second langage de types.

`ExtensionRegistry.prepare(id, checker, version=None)` :

1. construit les codecs des signatures du manifeste ;
2. cherche les contrats par leur identifiant exact dans `SchemaRegistry` ;
3. prouve **type d'entrée ⊆ contrat d'entrée**, puis **contrat de sortie ⊆ type de sortie** ;
4. rend `PreparedExtension` avec métadonnées copiées et codecs ; `encode_input` et
   `decode_output` valident aussi les données concrètes contre le contrat déclaré.

Cette étape n'importe ni ne charge le backend. Les futurs adaptateurs de HYP-044 devront
passer par cette préparation et ces validations de données. Le chargement actuel des
adaptateurs M2 n'est pas présenté comme un nouveau chargeur d'extensions.
`plugins list|show` reste une inspection de métadonnées, même sans les contrats installés.

## Vérification conservatrice des contrats

Le vérificateur établit une inclusion suffisante, pas l'équivalence de tout JSON Schema.
Son sous-ensemble structurel comprend :

- scalaires (`integer` inclus dans `number`), bornes numériques inclusives/exclusives,
  longueurs de chaînes et tableaux ;
- constantes et énumérations finies ;
- objets fermés, champs et propriétés requises ;
- tableaux homogènes et tuples ;
- `anyOf`, et `oneOf` d'objets à étiquettes constantes distinctes et requises ;
- références JSON Pointer locales et références absolues à des ressources déjà enregistrées.

La récursion régulière est traitée par obligations structurelles mémorisées. L'algorithme
peut refuser une inclusion pourtant vraie lorsqu'aucune règle suffisante ne la démontre
(exemple : une union cible couvre ensemble un domaine qu'aucune branche ne couvre seule).
Les annotations sans effet de validation sont ignorées ; les mots-clés sémantiques non
implémentés (`pattern`, `format`, `allOf`, `not`, `if`, `multipleOf`, etc.), les objets
ouverts, les tableaux de `type`, les changements de ressource par `$id` imbriqué,
les références relatives, les `$ref` avec contraintes sœurs et les unions non disjointes
en `oneOf` sont refusés avec `UnsupportedSchemaError`.
Une incompatibilité structurelle produit `CompatibilityError`. Un contrat absent est
une `ContractError`, jamais une récupération HTTP ni une acceptation par défaut.

Un contrat de sortie `number` non borné n'est pas prouvé décodable comme `float` :
il autorise aussi des entiers arbitrairement grands. Déclarer les bornes finies du codec
ou un sous-intervalle. Une entrée `int` sans raffinement ne garantit pas une borne telle
que `minimum: 0` : ce contrat d'entrée est refusé statiquement, même si certaines valeurs
concrètes conviendraient. Les types raffinés ne sont pas inventés dans cette tâche.

## Migration et conséquences

Changement volontaire de format, sans mode de compatibilité silencieux :

- `engine.bridge.to_json` et `core.to_json` gardent désormais les étiquettes des options ;
- la bibliothèque `Json.t` ajoute `Int of int` **en fin** de déclaration, sans déplacer
  les indices précédents ; `Num of float` reste un flottant ;
- `python_to_json` choisit `Int` pour un entier et `Num` pour un flottant ;
  `json_to_python` ne transforme plus `5.0` en `5` ;
- `Json.int` donne un entier exact ; `Json.num` conserve la lecture numérique courante
  et convertit explicitement les `Int` en flottants ;
- les attentes du banc mécanique sont migrées vers les options étiquetées ; aucun
  développement LLM supplémentaire ;
- les contrats capteurs/actionneurs mécanique et ventilation n'exposent pas d'option :
  aucun changement artificiel de leurs schémas ou adaptateurs n'est nécessaire ;
- les explications textuelles conservent désormais `.0` sur les valeurs flottantes.

Les documents JSON persistés dans l'ancien format ne sont pas décodés implicitement comme
le nouveau. Tout consommateur externe d'options doit migrer explicitement son contrat.

## Vérification et frontière formelle

Hypothesis vérifie `decode(encode(v)) == v` après `json.dumps(allow_nan=False)` et
`json.loads`, la conformité au schéma et l'accord des ponts sur types composés et récursifs.
Les tests couvrent les refus, la direction des inclusions, l'inspection sans import et
les effets des deux langages M2 existants.

Aucune modification de la Core IR ni des règles de l'interpréteur : `Json.Int` est un
constructeur de bibliothèque, pas une nouvelle forme IR. La primitive Python `core.to_json`
et le codec JSON ne font pas partie des primitives entières modélisées en Lean. Cette
frontière est explicitée dans le catalogue et la documentation formelle ; aucune nouvelle
propriété JSON n'est déclarée prouvée. Les preuves d'aller-retour dédiées restent HYP-043.
