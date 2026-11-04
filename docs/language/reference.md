# Référence du langage — sous-ensemble V0

Hypomnesis reprend la syntaxe d'OCaml. Ce document liste ce que le prototype accepte
aujourd'hui ; tout ce qui n'y figure pas est hors périmètre de la V0.

## Éléments de premier niveau

```ocaml
let x = 1                              (* valeur *)
let f a b = a + b                      (* fonction, paramètres curryfiés *)
let rec even n = n = 0 || odd (n - 1)
and odd n = n <> 0 && even (n - 1)     (* récursion mutuelle *)
let (q, r) = (7 / 2, 7 mod 2)          (* déstructuration *)
let a, b = 1, 2

type meters = float                                    (* abréviation *)
type 'a tree = Leaf | Node of 'a tree * 'a * 'a tree   (* variant *)
type ('k, 'v) entry = { key : 'k; value : 'v }         (* record *)
type a = A of b | Nil and b = { next : a }             (* types mutuellement récursifs *)

module Geometry = struct ... end
open Geometry
external sqrt : float -> float = "float.sqrt"          (* primitive du registre natif *)
```

## Expressions

| Forme | Exemple |
|---|---|
| Littéraux | `42`, `1_000`, `3.14`, `2e3`, `"texte"`, `true`, `()` |
| Fonctions | `fun x y -> x + y`, `fun (a, b) -> a`, `function [] -> 0 \| _ -> 1` |
| Liaison locale | `let x = 1 in x + 1`, `let rec f n = ... in f 10` |
| Conditionnelle | `if c then a else b` (le `else` est obligatoire) |
| Filtrage | `match e with p1 -> e1 \| p2 when cond -> e2` |
| Tuples, listes | `(1, "a")`, `1, "a"`, `[1; 2; 3]`, `x :: xs` |
| Records | `{ width = 1.0; height = 2.0 }`, `{ p with width = 3.0 }`, `p.width`, `{ M.field = ... }` |
| Constructeurs | `None`, `Some 3`, `Node (l, v, r)` ; un constructeur seul est une fonction |
| Annotation | `(e : int list)` |
| Opérateur comme valeur | `List.fold_left ( + ) 0 xs` |

### Précédence (de la plus faible à la plus forte)

| Niveau | Opérateurs | Associativité |
|---|---|---|
| `let`, `fun`, `function`, `if`, `match` | — | s'étendent le plus loin possible |
| `,` | tuple | — |
| `@@` | application | droite |
| `\|>` | pipe | gauche |
| `\|\|` | ou logique (court-circuit) | droite |
| `&&` | et logique (court-circuit) | droite |
| `=` `<>` `<` `>` `<=` `>=` | comparaison structurelle | gauche |
| `::` `@` `^` | cons, concaténation | droite |
| `+` `-` `+.` `-.` | addition | gauche |
| `*` `/` `mod` `*.` `/.` | multiplication | gauche |
| `**` | puissance flottante | droite |
| `-` `-.` (préfixe) | négation | — |
| application | `f x y` | gauche |
| `.` | accès à un champ | gauche |

Les opérateurs entiers et flottants sont distincts, comme en OCaml (`+` contre `+.`).

## Motifs

`_`, variables, littéraux (y compris négatifs), constructeurs, tuples (avec ou sans
parenthèses), listes `[a; b]`, `h :: t`, records `{ width; height = h }` (champs omis
autorisés), alternatives `A | B`, alias `p as x`, annotations `(p : t)`.

Une alternative doit lier les mêmes variables avec les mêmes types des deux côtés.

## Types

Types de base : `int`, `float`, `string`, `bool`, `unit`, `'a list`. Le prélude définit
`'a option` et `('a, 'e) result`. Notation : `int -> int`, `int * string`, `'a list option`,
`(int, string) result`, `Length.t`.

## Sémantique

- Évaluation stricte, valeurs immuables, fermetures lexicales.
- Égalité et comparaison structurelles ; comparer des fonctions est une erreur d'exécution.
- Division entière tronquée vers zéro (comme OCaml).
- Les appels terminaux s'exécutent en pile constante.
- Erreurs d'exécution : `Match_failure`, `Division_by_zero`, `Failure` (`failwith`).

## Prélude

- Fonctions : `not`, `id`, `const`, `flip`, `compose`, `fst`, `snd`, `min`, `max`, `compare`,
  `failwith`, `ignore`, conversions `string_of_int`, `float_of_int`, `int_of_float`, …
- Modules : `List` (`map`, `filter`, `fold_left`, `fold_right`, `sort`, `range`, `assoc_opt`,
  `find_opt`, `zip`, …), `Option`, `Result`, `String`, `Int`, `Float`.

Le prélude est écrit en Hypomnesis : [`src/hypomnesis/stdlib/prelude.hyp`](../../src/hypomnesis/stdlib/prelude.hyp).

### Frontière JSON (HYP-042)

`to_json` construit un `Json.t` : `Int of int` préserve les entiers exacts et `Num of float`
les flottants finis. `Json.int` lit un entier sans conversion ; `Json.num` lit un flottant
ou convertit explicitement un entier en flottant. `Some x` et `None` ne sont **plus effacés** :
ils deviennent les objets étiquetés `{"tag":"Some","arg":...}` et `{"tag":"None"}`.
Cela distingue `None`, `Some ()` et les options imbriquées. Les records deviennent des objets,
les listes/tuples des tableaux et `()` devient `null`. Les fonctions et nombres non finis
sont refusés.

L'API Python `TypeCodec(checker, signature)` génère un JSON Schema et encode/décode les
types clos avec contrôle strict ; voir l'[ADR 0010](../adr/0010-types-et-json-reversible.md)
pour la migration et les limites de vérification statique des contrats.

## Descriptions (langages M2)

Un commentaire `(** … *)` placé juste avant une déclaration (module, type, champ, constructeur,
valeur) la décrit ; les lignes `@nom texte` sont des balises (`@quand`, `@unité`, `@exemple`,
`@interne`, `@discret`, …). Pour la grammaire c'est un commentaire : aucun effet sémantique.
Un langage M2 est refusé au chargement si un élément **public** (aucun composant du nom ne commence
par `_`) n'a pas de description ; `@interne` retire un élément décrit du catalogue du prompt, et
`@discret` garde un champ dans le catalogue sans sa description. Les programmes M1 en sont exempts.
Voir l'ADR 0009.

## Couches de langages et imports

Un fichier d'entrée `.hyp` peut déclarer une couche symbolique. Par convention, un dossier
de langage contient `langage.hyp`. La déclaration `language` doit être le premier élément,
unique et hors de tout module :

```ocaml
language exemple = {
  version = "1.0.0";
  description = "Un langage construit sur des couches communes.";
  imports = ["../booleen"; "../arithmetique/langage.hyp"];
  sources = ["definitions.hyp"];
  adapters = ["adaptateurs/io.py"];
  contracts = ["contrats/commande.json"];
  procedure = { kind = "program"; entry = "procedure" }
}
```

- `version` est obligatoire. `description`, `imports`, `sources`, `adapters`, `contracts`,
  `examples` et `procedure` sont optionnels. Les champs inconnus ou dupliqués sont refusés.
- Les données de configuration sont statiques : chaînes, entiers, booléens, listes
  séparées par `;`, records de champs `cle = valeur` (clés chaînes possibles).
  Aucune expression, fonction, interpolation ou import Python n'est évalué pour les lire.
- `imports` contient des chemins **relatifs** de dossiers ou fichiers `.hyp` d'entrée.
  Les imports transitifs sont résolus avant les définitions de la couche.
  Les chemins canoniques dédupliquent les diamants ; cycles, identités dupliquées et
  collisions d'exports entre couches sont refusés. Une branche ne peut utiliser les
  imports d'une autre branche qu'elle ne déclare pas.
- Les définitions gardent les espaces de noms des modules existants ; les exports
  transitifs sont disponibles sous leurs noms qualifiés. Il n'y a pas de renommage
  d'import ni de nouvelle règle de visibilité privée.
- Le corps du fichier d'entrée, après `language`, précède les fichiers `sources`,
  chargés dans l'ordre. Ces fichiers ne redéclarent pas de couche et doivent rester
  dans le paquet, comme les contrats, exemples et modules d'adaptateurs.
- Sans `procedure`, la couche est une bibliothèque importable, pas un programme exécutable.
  Les configurations d'entrées/sorties ne sont pas héritées implicitement des imports.

Les anciens `langage.json` ne sont plus acceptés. Migrer leurs métadonnées vers la déclaration
native et remplacer les références Python `fichier.py:fonction` par des modules dans
`adapters` et des décorateurs sur leurs fonctions.

```bash
hypomnesis check chemin/langage.hyp
hypomnesis check programme.hyp --langage chemin/du/langage --format json
hypomnesis layers chemin/du/langage
```

`layers` exporte du JSON versionné : nœuds identifiés par nom de couche, arêtes
`from` → `to` orientées **dépendance vers utilisateur**, et générations topologiques
dans `layers`. Il ne charge aucun code Python d'entrée/sortie et n'évalue pas de programme.
Les chemins d'entrée absolus de l'export identifient les sources locales ; le graphe
est déterministe pour un même ensemble de fichiers.

### Entrées et sorties Python

Seuls les modules explicitement déclarés dans `adapters` sont inspectés, au moment de
l'exécution ou d'une demande de transcription. Ils utilisent :

```python
from hypomnesis.engine.adapters import actuator, environment, sensor, transcriber


@environment
def creer_environnement(options, dossier_sortie):
    return MonEnvironnement(options, dossier_sortie)


@sensor("mon-capteur")
def lire(env, identifiant):
    return env.message(identifiant)


@actuator("mon-actionneur")
def creer_actionneur(env):
    return MonActionneur(env)  # une valeur hypomnesis.effects.dispatcher.Actuator


@transcriber
def transcrire(demande):
    return produire_programme(demande)
```

Un lecteur de capteur renvoie une enveloppe de message validée par les contrats ; une
fabrique d'actionneur doit renvoyer un `Actuator` du même identifiant que son décorateur.
Les permissions et contrats du dispatcher continuent de contrôler toute action.
En l'absence d'environnement, les fabriques d'actionneurs reçoivent le dossier de sortie
et les lecteurs de capteurs reçoivent `None`. Chaque rôle capteur/actionneur a des
identifiants uniques ; environnement et transcription sont uniques par langage.
Les signatures incompatibles et fonctions asynchrones ne sont pas acceptées.
Les décorateurs ne modifient pas les fonctions et n'enregistrent aucun état global.
`check` et le LSP n'importent jamais ces modules et n'exécutent aucune définition éditée.
Ils peuvent donc vérifier une bibliothèque sans ses dépendances Python d'exécution.

Les exemples complets sont dans `demo/languages/booleen`, `arithmetique`, `contraintes`,
`composition_a` et `composition_b` ; les deux derniers réutilisent les mêmes couches.

## Pas encore implémenté

Signatures de modules et foncteurs, registre distant et versions d'import,
opérateurs définis par l'utilisateur, exceptions rattrapables, vérification
d'exhaustivité du filtrage, macros, types dimensionnels, effets.
