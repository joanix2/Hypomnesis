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
* `binop` ↔ application des primitives `int.add`, `poly.eq`, ...

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
  deriving DecidableEq, Repr

inductive BinOp where
  | add | sub | mul | eq | lt
  deriving DecidableEq, Repr

/-- Type du résultat d'une primitive binaire (les opérandes sont entières). -/
def BinOp.result : BinOp → Ty
  | .add | .sub | .mul => .int
  | .eq | .lt => .bool

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
  deriving Repr

abbrev Ctx := List Ty

end Hypomnesis.Core
