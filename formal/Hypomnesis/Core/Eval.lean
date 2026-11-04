import Hypomnesis.Core.Syntax

/-!
# Sémantique de référence

Interpréteur à environnements et fermetures, comme `runtime/interpreter.py`.
Le paramètre `fuel` borne le nombre d'étapes : il rend la fonction totale
(Lean l'exige) et modélise les budgets de calcul du §11 du cahier des
charges. Un résultat est une valeur, `timeout` (budget épuisé), `matchFail`
(aucun motif ne s'applique : `Match_failure` de l'interpréteur Python) ou
`stuck` (erreur d'exécution : c'est ce que le typage doit exclure).
-/

namespace Hypomnesis.Core

inductive Val where
  | int (n : Int)
  | bool (b : Bool)
  | float (f : Float)
  | string (s : String)
  | unit
  | clo (env : List Val) (body : Expr)
  | rclo (env : List Val) (body : Expr)
  | pair (fst snd : Val)
  | con (c : Nat) (arg : Val)
  deriving Repr

inductive Res where
  | ok (v : Val)
  | stuck
  | timeout
  | matchFail
  | error (message : String)
  deriving Repr

def Res.bind : Res → (Val → Res) → Res
  | .ok v, k => k v
  | .stuck, _ => .stuck
  | .timeout, _ => .timeout
  | .matchFail, _ => .matchFail
  | .error message, _ => .error message

def floatCompare (a b : Float) : Int :=
  if a.isNaN then (if b.isNaN then 0 else -1)
  else if b.isNaN then 1 else if a < b then -1 else if b < a then 1 else 0

def evalOp : BinOp → Val → Val → Res
  | .add, .int a, .int b => .ok (.int (a + b))
  | .sub, .int a, .int b => .ok (.int (a - b))
  | .mul, .int a, .int b => .ok (.int (a * b))
  | .div, .int a, .int b =>
    if b == 0 then .error "Division_by_zero" else .ok (.int (a.tdiv b))
  | .mod, .int a, .int b =>
    if b == 0 then .error "Division_by_zero" else .ok (.int (a.tmod b))
  | .eq, .int a, .int b => .ok (.bool (decide (a = b)))
  | .lt, .int a, .int b => .ok (.bool (decide (a < b)))
  | .fadd, .float a, .float b => .ok (.float (a + b))
  | .fsub, .float a, .float b => .ok (.float (a - b))
  | .fmul, .float a, .float b => .ok (.float (a * b))
  | .fdiv, .float a, .float b => .ok (.float (a / b))
  | .feq, .float a, .float b => .ok (.bool (a == b))
  | .flt, .float a, .float b => .ok (.bool (floatCompare a b < 0))
  | .fle, .float a, .float b => .ok (.bool (floatCompare a b <= 0))
  | .fcompare, .float a, .float b => .ok (.int (floatCompare a b))
  | .sconcat, .string a, .string b => .ok (.string (a ++ b))
  | .seq, .string a, .string b => .ok (.bool (a == b))
  | .slt, .string a, .string b => .ok (.bool (a < b))
  | .scompare, .string a, .string b =>
    .ok (.int (if a < b then -1 else if b < a then 1 else 0))
  | _, _, _ => .stuck

/-- Filtrage : les valeurs liées, la plus récente d'abord, ou `none`. -/
def matchPat : Pat → Val → Option (List Val)
  | .wild, _ => some []
  | .var, v => some [v]
  | .int n, .int m => if n = m then some [] else none
  | .bool b, .bool b' => if b = b' then some [] else none
  | .float a, .float b => if a == b then some [] else none
  | .string a, .string b => if a == b then some [] else none
  | .pair p₁ p₂, .pair a b =>
    match matchPat p₁ a, matchPat p₂ b with
    | some vs₁, some vs₂ => some (vs₂ ++ vs₁)
    | _, _ => none
  | .ctor c p, .con c' v => if c = c' then matchPat p v else none
  | _, _ => none

def eval : Nat → List Val → Expr → Res
  | 0, _, _ => .timeout
  | n + 1, env, e =>
    match e with
    | .var i =>
      match env[i]? with
      | some v => .ok v
      | none => .stuck
    | .int k => .ok (.int k)
    | .bool b => .ok (.bool b)
    | .float f => .ok (.float f)
    | .string s => .ok (.string s)
    | .unit => .ok .unit
    | .lam _ b => .ok (.clo env b)
    | .fix _ _ b => .ok (.rclo env b)
    | .app f a =>
      (eval n env f).bind fun fv =>
      (eval n env a).bind fun av =>
        match fv with
        | .clo cenv b => eval n (av :: cenv) b
        | .rclo cenv b => eval n (av :: fv :: cenv) b
        | _ => .stuck
    | .letE x b => (eval n env x).bind fun v => eval n (v :: env) b
    | .ite c a b =>
      (eval n env c).bind fun cv =>
        match cv with
        | .bool true => eval n env a
        | .bool false => eval n env b
        | _ => .stuck
    | .pair a b =>
      (eval n env a).bind fun va =>
      (eval n env b).bind fun vb => .ok (.pair va vb)
    | .fst x =>
      (eval n env x).bind fun v =>
        match v with
        | .pair a _ => .ok a
        | _ => .stuck
    | .snd x =>
      (eval n env x).bind fun v =>
        match v with
        | .pair _ b => .ok b
        | _ => .stuck
    | .binop op a b =>
      (eval n env a).bind fun va =>
      (eval n env b).bind fun vb =>
        evalOp op va vb
    | .construct _ c x => (eval n env x).bind fun v => .ok (.con c v)
    | .case x p e₁ e₂ =>
      (eval n env x).bind fun v =>
        match matchPat p v with
        | some vs => eval n (vs ++ env) e₁
        | none => eval n env e₂
    | .fail _ => .matchFail
    | .raise _ message =>
      (eval n env message).bind fun v =>
        match v with
        | .string s => .error ("Failure: " ++ s)
        | _ => .stuck

end Hypomnesis.Core
