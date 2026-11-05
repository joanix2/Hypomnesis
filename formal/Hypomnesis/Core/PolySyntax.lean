import Hypomnesis.Core.PolyTypes
import Hypomnesis.Core.Eval

/-!
# Expressions annotées par des schémas de rang 1 (HYP-023)

Cette syntaxe est une frontière d'élaboration vers l'évaluateur Core :
les let polymorphes lient un schéma et les variables portent leurs arguments
de types explicites. `erase` réutilise la syntaxe d'exécution existante ; il
n'introduit pas un second évaluateur.
-/

namespace Hypomnesis.Core.Poly

inductive Expr where
  | var (index : Nat) (typeArgs : List Ty)
  | int (value : Int)
  | bool (value : Bool)
  | float (value : Float)
  | string (value : String)
  | unit
  | lam (domain : Ty) (body : Expr)
  | fix (domain codomain : Ty) (body : Expr)
  | app (fn arg : Expr)
  | letE (scheme : Scheme) (value body : Expr)
  | ite (condition thenBranch elseBranch : Expr)
  | pair (fst snd : Expr)
  | fst (expr : Expr)
  | snd (expr : Expr)
  | binop (op : BinOp) (lhs rhs : Expr)
  | construct (data ctor : Nat) (typeArgs : List Ty) (arg : Expr)
  | case (scrutinee : Expr) (pattern : Pat) (onMatch onFail : Expr)
  | fail (type : Ty)
  | raise (type : Ty) (message : Expr)
  deriving Repr

def Expr.subst (σ : Nat → Ty) : Expr → Expr
  | .var index args => .var index (args.map (Ty.subst σ))
  | .int value => .int value
  | .bool value => .bool value
  | .float value => .float value
  | .string value => .string value
  | .unit => .unit
  | .lam domain body => .lam (domain.subst σ) (body.subst σ)
  | .fix domain codomain body =>
    .fix (domain.subst σ) (codomain.subst σ) (body.subst σ)
  | .app fn arg => .app (fn.subst σ) (arg.subst σ)
  | .letE scheme value body =>
    .letE (scheme.subst σ) (value.subst (lift scheme.arity σ)) (body.subst σ)
  | .ite condition thenBranch elseBranch =>
    .ite (condition.subst σ) (thenBranch.subst σ) (elseBranch.subst σ)
  | .pair left right => .pair (left.subst σ) (right.subst σ)
  | .fst expr => .fst (expr.subst σ)
  | .snd expr => .snd (expr.subst σ)
  | .binop op lhs rhs => .binop op (lhs.subst σ) (rhs.subst σ)
  | .construct data ctor args arg =>
    .construct data ctor (args.map (Ty.subst σ)) (arg.subst σ)
  | .case scrutinee pattern onMatch onFail =>
    .case (scrutinee.subst σ) pattern (onMatch.subst σ) (onFail.subst σ)
  | .fail type => .fail (type.subst σ)
  | .raise type message => .raise (type.subst σ) (message.subst σ)

private theorem substArgs_var (args : List Ty) :
    args.map (Ty.subst Ty.var) = args := by
  induction args with
  | nil => rfl
  | cons arg args ih => simp [Ty.subst_var, ih]

def Expr.erase : Expr → Hypomnesis.Core.Expr
  | .var index _ => .var index
  | .int value => .int value
  | .bool value => .bool value
  | .float value => .float value
  | .string value => .string value
  | .unit => .unit
  | .lam _ body => .lam .unit body.erase
  | .fix _ _ body => .fix .unit .unit body.erase
  | .app fn arg => .app fn.erase arg.erase
  | .letE _ value body => .letE value.erase body.erase
  | .ite condition thenBranch elseBranch =>
    .ite condition.erase thenBranch.erase elseBranch.erase
  | .pair left right => .pair left.erase right.erase
  | .fst expr => .fst expr.erase
  | .snd expr => .snd expr.erase
  | .binop op lhs rhs => .binop op lhs.erase rhs.erase
  | .construct data ctor _ arg => .construct data ctor arg.erase
  | .case scrutinee pattern onMatch onFail =>
    .case scrutinee.erase pattern onMatch.erase onFail.erase
  | .fail _ => .fail .unit
  | .raise _ message => .raise .unit message.erase

@[simp] theorem Expr.subst_var (expr : Expr) : expr.subst Ty.var = expr := by
  induction expr <;>
    simp_all [Expr.subst, Ty.subst_var, Scheme.subst_var, lift_var, substArgs_var]

theorem Expr.erase_subst (expr : Expr) (σ : Nat → Ty) :
    (expr.subst σ).erase = expr.erase := by
  induction expr generalizing σ <;> simp_all [Expr.subst, Expr.erase]

theorem Expr.eval_erase_subst (fuel : Nat) (env : List Core.Val)
    (expr : Expr) (σ : Nat → Ty) :
    Core.eval fuel env (expr.subst σ).erase = Core.eval fuel env expr.erase := by
  rw [Expr.erase_subst]

theorem Expr.eval_erase_subst_ne_stuck (fuel : Nat) (env : List Core.Val)
    (expr : Expr) (σ : Nat → Ty)
    (hsafe : Core.eval fuel env expr.erase ≠ .stuck) :
    Core.eval fuel env (expr.subst σ).erase ≠ .stuck := by
  rw [Expr.eval_erase_subst]
  exact hsafe

end Hypomnesis.Core.Poly
