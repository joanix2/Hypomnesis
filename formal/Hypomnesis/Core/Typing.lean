import Hypomnesis.Core.Syntax

/-! # Typage déclaratif du fragment -/

namespace Hypomnesis.Core

inductive HasType : Ctx → Expr → Ty → Prop where
  | var {Γ i t} : Γ[i]? = some t → HasType Γ (.var i) t
  | int {Γ n} : HasType Γ (.int n) .int
  | bool {Γ b} : HasType Γ (.bool b) .bool
  | unit {Γ} : HasType Γ .unit .unit
  | lam {Γ t₁ t₂ b} : HasType (t₁ :: Γ) b t₂ → HasType Γ (.lam t₁ b) (.arrow t₁ t₂)
  | fix {Γ t₁ t₂ b} :
      HasType (t₁ :: .arrow t₁ t₂ :: Γ) b t₂ → HasType Γ (.fix t₁ t₂ b) (.arrow t₁ t₂)
  | app {Γ f a t₁ t₂} :
      HasType Γ f (.arrow t₁ t₂) → HasType Γ a t₁ → HasType Γ (.app f a) t₂
  | letE {Γ e b t₁ t₂} : HasType Γ e t₁ → HasType (t₁ :: Γ) b t₂ → HasType Γ (.letE e b) t₂
  | ite {Γ c a b t} :
      HasType Γ c .bool → HasType Γ a t → HasType Γ b t → HasType Γ (.ite c a b) t
  | pair {Γ a b t₁ t₂} :
      HasType Γ a t₁ → HasType Γ b t₂ → HasType Γ (.pair a b) (.prod t₁ t₂)
  | fst {Γ e t₁ t₂} : HasType Γ e (.prod t₁ t₂) → HasType Γ (.fst e) t₁
  | snd {Γ e t₁ t₂} : HasType Γ e (.prod t₁ t₂) → HasType Γ (.snd e) t₂
  | binop {Γ op a b} :
      HasType Γ a .int → HasType Γ b .int → HasType Γ (.binop op a b) op.result

end Hypomnesis.Core
