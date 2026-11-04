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

## Descriptions (langages M2)

Un commentaire `(** … *)` placé juste avant une déclaration (module, type, champ, constructeur,
valeur) la décrit ; les lignes `@nom texte` sont des balises (`@quand`, `@unité`, `@exemple`,
`@interne`, `@discret`, …). Pour la grammaire c'est un commentaire : aucun effet sémantique.
Un langage M2 est refusé au chargement si un élément **public** (aucun composant du nom ne commence
par `_`) n'a pas de description ; `@interne` retire un élément décrit du catalogue du prompt, et
`@discret` garde un champ dans le catalogue sans sa description. Les programmes M1 en sont exempts.
Voir l'ADR 0009.

## Pas encore implémenté

Signatures de modules et foncteurs, import entre fichiers (la CLI charge les fichiers dans
l'ordre donné), opérateurs définis par l'utilisateur, exceptions rattrapables, vérification
d'exhaustivité du filtrage, macros, types dimensionnels, effets.
