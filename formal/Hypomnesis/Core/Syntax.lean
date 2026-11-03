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

Annotations (HYP-024). Les types portés ici par la syntaxe viennent des
annotations que le vérificateur Python ajoute à sa Core IR : `lam dom` ↔
`Lambda.param_types`, `fix dom cod` ↔ `LetRec.types` / `DefRec.types`. Les
annotations Python liées au polymorphisme (`forall_vars`, `type_args`) n'ont
pas encore d'équivalent : elles seront formalisées avec HYP-023.
-/

namespace Hypomnesis.Core

inductive Ty where
  | int
  | bool
  | unit
  | arrow (dom cod : Ty)
  | prod (fst snd : Ty)
  | data (d : Nat)
  deriving DecidableEq, Repr

/-- Signature : pour chaque instance de type de données, le type de l'argument
de chacun de ses constructeurs (dans l'ordre de déclaration). -/
abbrev Sig := List (List Ty)

inductive BinOp where
  | add | sub | mul | eq | lt
  deriving DecidableEq, Repr

/-- Type du résultat d'une primitive binaire (les opérandes sont entières). -/
def BinOp.result : BinOp → Ty
  | .add | .sub | .mul => .int
  | .eq | .lt => .bool

/-- Motifs. Les variables liées sont rangées dans l'ordre de l'environnement :
la plus récente d'abord (les variables de `p₂` précèdent celles de `p₁`
dans `pair p₁ p₂`). -/
inductive Pat where
  | wild
  | var
  | int (n : Int)
  | bool (b : Bool)
  | pair (fst snd : Pat)
  | ctor (c : Nat) (arg : Pat)
  deriving Repr

inductive Expr where
  | var (i : Nat)
  | int (n : Int)
  | bool (b : Bool)
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
  deriving Repr

abbrev Ctx := List Ty

end Hypomnesis.Core
