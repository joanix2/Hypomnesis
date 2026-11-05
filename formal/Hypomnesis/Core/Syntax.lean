/-!
# Core IR — fragment formalisé

Fragment de la Core IR (`src/hypomnesis/ir/core.py`) après élaboration :
les variables sont des indices de de Bruijn et les paramètres de fonction
portent leur type (c'est ce que produira le certificat émis par le
vérificateur Python, cf. `docs/verification/strategie.md`).

Correspondance avec la Core IR Python :
* `lam`   ↔ `Lambda` à un paramètre ;
* `fix`   ↔ `LetRec` d'une fonction (indice 0 = argument, 1 = la fonction) ;
* `letE`  ↔ `Let` ;
* `ite`   ↔ `Match` sur un booléen (forme élaborée de `if`) ;
* `pair`, `fst`, `snd` ↔ `Tuple` et filtrage de tuple ;
* `binop` ↔ application des primitives `int.add`, `poly.eq`, ... ;
* `construct d c e` ↔ `Construct` (constructeur `c` de l'instance `d`) ;
* `case x p e₁ e₂` et `fail t` ↔ `Match`, sous forme de chaîne binaire :
  `Match(s, [p₁ → b₁, p₂ → b₂])` devient
  `letE s (case (var 0) p₁ b₁ (case (var 0) p₂ b₂ (fail t)))`.

Types de données (HYP-020). La signature `Sig` est **monomorphisée** : son
entrée `d` est une instance de type de données (par exemple `int list`) et
donne le type de l'argument de chacun de ses constructeurs, sans paramètre.
Un constructeur nullaire prend `unit`. Exemple, `int list` à l'indice `d` :
`[unit, prod int (data d)]` pour `[]` et `::`. L'instanciation des types
paramétrés est faite par le décodeur des certificats, en dehors du noyau
prouvé.

Records nominaux (HYP-021). Une instance est une donnée à constructeur unique,
dont l'argument est le produit des champs terminé par unit. `Records.lean`
définit construction, accès et mise à jour comme formes dérivées typées :
elles héritent de la sûreté et de la correction/complétude du vérificateur.
Le décodeur traduit les motifs records en motifs de constructeur et de produit,
en préservant les variables de l'ordre source.

Annotations (HYP-024/HYP-023). Les types portés ici par la syntaxe viennent
des annotations que le vérificateur Python ajoute à sa Core IR : `lam dom` ↔
`Lambda.param_types`, `fix dom cod` ↔ `LetRec.types` / `DefRec.types`. La
syntaxe parallèle `Poly.Expr` représente `type_args` aux variables et le
schéma `forall_vars` au `let`; `Poly.Expr.erase` les efface avant le véritable
`Core.eval`. En particulier, `Poly.Expr.erase` efface les annotations lambda
à `unit`, ce qui préserve l'invariance de substitution. Pour le fragment
runtime monomorphe, `Poly.Expr.eraseMono` conserve les annotations lambda ;
`PolySoundness.Expr.eval_eraseMono_eq_erase` prouve l'égalité d'évaluation au
véritable `Core.eval` quand le corps des fermetures a le même effacement.
Le pont de sûreté couvre les variables à arguments de types vides, les `let`
monomorphes et les lambdas/applications monomorphes ; les fonctions récursives,
les données paramétriques et les termes polymorphes multi-instanciés restent
hors preuve.

Scalaires (HYP-150). Float est binary64 (modèle logique Lean 4.35), String est
Unicode. BinOp fixe domaines et résultats ; raise produit une erreur explicite.
Le format de certificat 1.1 conserve les bits des littéraux flottants.

Frontière JSON (HYP-042, ADR 0010). `Json.Int` est un constructeur de bibliothèque
Python/Hypomnesis, pas une nouvelle forme IR. La primitive `core.to_json` et les
codecs JSON restent hors du catalogue scalaire formalisé. HYP-043 prouve
l'aller-retour et la conformité au schéma dans le modèle séparé
`Contracts/Json.lean` : int/bool/string/unit, listes, paires, options et records
structurels finis. Ni binary64 ni références récursives couverts par ces preuves.
-/

namespace Hypomnesis.Core

inductive Ty where
  | int
  | bool
  | float
  | string
  | unit
  | arrow (dom cod : Ty)
  | prod (fst snd : Ty)
  | data (d : Nat)
  deriving DecidableEq, Repr

/-- Signature : pour chaque instance de type de données, le type de l'argument
de chacun de ses constructeurs (dans l'ordre de déclaration). -/
abbrev Sig := List (List Ty)

inductive BinOp where
  | add | sub | mul | div | mod | eq | lt
  | fadd | fsub | fmul | fdiv | feq | flt | fle | fcompare
  | sconcat | seq | slt | scompare
  deriving DecidableEq, Repr

/-- Signatures fermées : le certificat ne choisit pas les types des primitives. -/
def BinOp.domain : BinOp → Ty
  | .fadd | .fsub | .fmul | .fdiv | .feq | .flt | .fle | .fcompare => .float
  | .sconcat | .seq | .slt | .scompare => .string
  | _ => .int

def BinOp.result : BinOp → Ty
  | .add | .sub | .mul | .div | .mod | .fcompare | .scompare => .int
  | .fadd | .fsub | .fmul | .fdiv => .float
  | .sconcat => .string
  | _ => .bool

/-- Motifs. Les variables liées sont rangées dans l'ordre de l'environnement :
la plus récente d'abord (les variables de `p₂` précèdent celles de `p₁`
dans `pair p₁ p₂`). -/
inductive Pat where
  | wild
  | var
  | int (n : Int)
  | bool (b : Bool)
  | float (f : Float)
  | string (s : String)
  | pair (fst snd : Pat)
  | ctor (c : Nat) (arg : Pat)
  deriving Repr

inductive Expr where
  | var (i : Nat)
  | int (n : Int)
  | bool (b : Bool)
  | float (f : Float)
  | string (s : String)
  | unit
  | lam (dom : Ty) (body : Expr)
  | fix (dom cod : Ty) (body : Expr)
  | app (fn arg : Expr)
  | letE (value body : Expr)
  | ite (cond thn els : Expr)
  | pair (fst snd : Expr)
  | fst (e : Expr)
  | snd (e : Expr)
  | binop (op : BinOp) (lhs rhs : Expr)
  | construct (d c : Nat) (arg : Expr)
  /-- `case x p e₁ e₂` : si la valeur de `x` filtre `p`, `e₁` avec les variables
  du motif en tête de l'environnement ; sinon `e₂`. -/
  | case (scrutinee : Expr) (pat : Pat) (onMatch onFail : Expr)
  /-- Échec de filtrage (`Match_failure`), annoté par son type. -/
  | fail (t : Ty)
  | raise (t : Ty) (message : Expr)
  deriving Repr

abbrev Ctx := List Ty

end Hypomnesis.Core
