import Hypomnesis.Core.Syntax

/-!
# Sémantique de référence

Interpréteur à environnements et fermetures, comme `runtime/interpreter.py`.
Le paramètre `fuel` borne le nombre d'étapes : il rend la fonction totale
(Lean l'exige) et modélise les budgets de calcul du §11 du cahier des
charges. Un résultat est soit une valeur, soit `timeout` (budget épuisé),
soit `stuck` (erreur d'exécution : c'est ce que le typage doit exclure).
-/

namespace Hypomnesis.Core

inductive Val where
  | int (n : Int)
  | bool (b : Bool)
  | unit
  | clo (env : List Val) (body : Expr)
  | rclo (env : List Val) (body : Expr)
  | pair (fst snd : Val)
  deriving Repr

inductive Res where
  | ok (v : Val)
  | stuck
  | timeout
  deriving Repr

def Res.bind : Res → (Val → Res) → Res
  | .ok v, k => k v
  | .stuck, _ => .stuck
  | .timeout, _ => .timeout

def evalOp : BinOp → Int → Int → Val
  | .add, a, b => .int (a + b)
  | .sub, a, b => .int (a - b)
  | .mul, a, b => .int (a * b)
  | .eq, a, b => .bool (decide (a = b))
  | .lt, a, b => .bool (decide (a < b))

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
        match va, vb with
        | .int x, .int y => .ok (evalOp op x y)
        | _, _ => .stuck

end Hypomnesis.Core
