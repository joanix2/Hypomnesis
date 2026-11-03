import Hypomnesis.Core.Typing
import Hypomnesis.Core.Eval

/-!
# Sûreté du typage : « well-typed programs don't go wrong »

On type les valeurs runtime (`ValTy`) — une fermeture est bien typée si son
environnement capturé l'est et si son corps est bien typé dans le contexte
correspondant — puis on montre que l'évaluation d'un terme bien typé dans un
environnement bien typé ne rend jamais `stuck`, quel que soit le budget.
-/

namespace Hypomnesis.Core

mutual
  inductive ValTy : Val → Ty → Prop where
    | int {n} : ValTy (.int n) .int
    | bool {b} : ValTy (.bool b) .bool
    | unit : ValTy .unit .unit
    | clo {env Γ t₁ t₂ b} :
        EnvTy env Γ → HasType (t₁ :: Γ) b t₂ → ValTy (.clo env b) (.arrow t₁ t₂)
    | rclo {env Γ t₁ t₂ b} :
        EnvTy env Γ → HasType (t₁ :: .arrow t₁ t₂ :: Γ) b t₂ →
        ValTy (.rclo env b) (.arrow t₁ t₂)
    | pair {a b t₁ t₂} : ValTy a t₁ → ValTy b t₂ → ValTy (.pair a b) (.prod t₁ t₂)

  inductive EnvTy : List Val → Ctx → Prop where
    | nil : EnvTy [] []
    | cons {v t env Γ} : ValTy v t → EnvTy env Γ → EnvTy (v :: env) (t :: Γ)
end

/-- Un résultat est sûr à un type donné : valeur de ce type, ou budget épuisé. -/
def Safe : Res → Ty → Prop
  | .ok v, t => ValTy v t
  | .timeout, _ => True
  | .stuck, _ => False

theorem EnvTy.lookup {env : List Val} :
    ∀ {Γ : Ctx}, EnvTy env Γ →
      ∀ {i : Nat} {t : Ty}, Γ[i]? = some t → ∃ v, env[i]? = some v ∧ ValTy v t := by
  induction env with
  | nil => intro Γ h i t hi; cases h; simp at hi
  | cons v env ih =>
    intro Γ h i t hi
    cases h with
    | cons hv henv =>
      cases i with
      | zero => simp at hi; subst hi; exact ⟨_, rfl, hv⟩
      | succ i => simpa using ih henv (by simpa using hi)

theorem Safe.bind {r : Res} {k : Val → Res} {t₁ t₂ : Ty}
    (hr : Safe r t₁) (hk : ∀ v, ValTy v t₁ → Safe (k v) t₂) : Safe (r.bind k) t₂ := by
  cases r with
  | ok v => exact hk v hr
  | stuck => exact absurd hr id
  | timeout => trivial

theorem evalOp_ty (op : BinOp) (a b : Int) : ValTy (evalOp op a b) op.result := by
  cases op <;> constructor

/-- **Sûreté.** Pour tout budget, un terme bien typé évalué dans un
environnement bien typé ne se bloque pas, et toute valeur produite a le type
annoncé. -/
theorem eval_safe (n : Nat) :
    ∀ {env : List Val} {Γ : Ctx} {e : Expr} {t : Ty},
      EnvTy env Γ → HasType Γ e t → Safe (eval n env e) t := by
  induction n with
  | zero => intros; trivial
  | succ n ih =>
    intro env Γ e t henv ht
    cases ht with
    | var h =>
      obtain ⟨v, hv, hvt⟩ := henv.lookup h
      simp [eval, hv, Safe, hvt]
    | int => exact ValTy.int
    | bool => exact ValTy.bool
    | unit => exact ValTy.unit
    | lam hb => exact ValTy.clo henv hb
    | fix hb => exact ValTy.rclo henv hb
    | app hf ha =>
      refine Safe.bind (ih henv hf) fun fv hfv => Safe.bind (ih henv ha) fun av hav => ?_
      cases hfv with
      | clo henv' hb => exact ih (EnvTy.cons hav henv') hb
      | rclo henv' hb => exact ih (EnvTy.cons hav (EnvTy.cons (ValTy.rclo henv' hb) henv')) hb
    | letE hx hb =>
      exact Safe.bind (ih henv hx) fun v hv => ih (EnvTy.cons hv henv) hb
    | ite hc ha hb =>
      refine Safe.bind (ih henv hc) fun cv hcv => ?_
      cases hcv with
      | @bool b => cases b
                   · exact ih henv hb
                   · exact ih henv ha
    | pair ha hb =>
      exact Safe.bind (ih henv ha) fun va hva =>
        Safe.bind (ih henv hb) fun vb hvb => ValTy.pair hva hvb
    | fst hx =>
      refine Safe.bind (ih henv hx) fun v hv => ?_
      cases hv with
      | pair ha _ => exact ha
    | snd hx =>
      refine Safe.bind (ih henv hx) fun v hv => ?_
      cases hv with
      | pair _ hb => exact hb
    | binop ha hb =>
      refine Safe.bind (ih henv ha) fun va hva => Safe.bind (ih henv hb) fun vb hvb => ?_
      cases hva
      cases hvb
      exact evalOp_ty _ _ _

/-- Corollaire pour un programme clos : jamais `stuck`. -/
theorem closed_never_stuck {e : Expr} {t : Ty} (h : HasType [] e t) (n : Nat) :
    eval n [] e ≠ .stuck := by
  intro hstuck
  have hs := eval_safe n EnvTy.nil h
  rw [hstuck] at hs
  exact hs

end Hypomnesis.Core
