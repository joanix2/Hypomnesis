import Hypomnesis.Core.Syntax

/-! # Typage déclaratif du fragment, relativement à une signature `sig` -/

namespace Hypomnesis.Core

/-- `PatTy sig p t bs` : le motif `p` filtre des valeurs de type `t` et lie des
variables de types `bs` (la plus récente d'abord). -/
inductive PatTy (sig : Sig) : Pat → Ty → Ctx → Prop where
  | wild {t} : PatTy sig .wild t []
  | var {t} : PatTy sig .var t [t]
  | int {n} : PatTy sig (.int n) .int []
  | bool {b} : PatTy sig (.bool b) .bool []
  | float {f} : PatTy sig (.float f) .float []
  | string {s} : PatTy sig (.string s) .string []
  | pair {p₁ p₂ t₁ t₂ b₁ b₂} :
      PatTy sig p₁ t₁ b₁ → PatTy sig p₂ t₂ b₂ → PatTy sig (.pair p₁ p₂) (.prod t₁ t₂) (b₂ ++ b₁)
  | ctor {d c cs ta p bs} :
      sig[d]? = some cs → cs[c]? = some ta → PatTy sig p ta bs →
      PatTy sig (.ctor c p) (.data d) bs

inductive HasType (sig : Sig) : Ctx → Expr → Ty → Prop where
  | var {Γ i t} : Γ[i]? = some t → HasType sig Γ (.var i) t
  | int {Γ n} : HasType sig Γ (.int n) .int
  | bool {Γ b} : HasType sig Γ (.bool b) .bool
  | float {Γ f} : HasType sig Γ (.float f) .float
  | string {Γ s} : HasType sig Γ (.string s) .string
  | unit {Γ} : HasType sig Γ .unit .unit
  | lam {Γ t₁ t₂ b} : HasType sig (t₁ :: Γ) b t₂ → HasType sig Γ (.lam t₁ b) (.arrow t₁ t₂)
  | fix {Γ t₁ t₂ b} :
      HasType sig (t₁ :: .arrow t₁ t₂ :: Γ) b t₂ → HasType sig Γ (.fix t₁ t₂ b) (.arrow t₁ t₂)
  | app {Γ f a t₁ t₂} :
      HasType sig Γ f (.arrow t₁ t₂) → HasType sig Γ a t₁ → HasType sig Γ (.app f a) t₂
  | letE {Γ e b t₁ t₂} :
      HasType sig Γ e t₁ → HasType sig (t₁ :: Γ) b t₂ → HasType sig Γ (.letE e b) t₂
  | ite {Γ c a b t} :
      HasType sig Γ c .bool → HasType sig Γ a t → HasType sig Γ b t →
      HasType sig Γ (.ite c a b) t
  | pair {Γ a b t₁ t₂} :
      HasType sig Γ a t₁ → HasType sig Γ b t₂ → HasType sig Γ (.pair a b) (.prod t₁ t₂)
  | fst {Γ e t₁ t₂} : HasType sig Γ e (.prod t₁ t₂) → HasType sig Γ (.fst e) t₁
  | snd {Γ e t₁ t₂} : HasType sig Γ e (.prod t₁ t₂) → HasType sig Γ (.snd e) t₂
  | binop {Γ op a b} :
      HasType sig Γ a op.domain → HasType sig Γ b op.domain →
      HasType sig Γ (.binop op a b) op.result
  | construct {Γ d c cs ta e} :
      sig[d]? = some cs → cs[c]? = some ta → HasType sig Γ e ta →
      HasType sig Γ (.construct d c e) (.data d)
  | case {Γ x p e₁ e₂ tx bs t} :
      HasType sig Γ x tx → PatTy sig p tx bs → HasType sig (bs ++ Γ) e₁ t →
      HasType sig Γ e₂ t → HasType sig Γ (.case x p e₁ e₂) t
  | fail {Γ t} : HasType sig Γ (.fail t) t
  | raise {Γ t message} :
      HasType sig Γ message .string → HasType sig Γ (.raise t message) t

end Hypomnesis.Core
