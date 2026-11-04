import Hypomnesis.Core.Typing
import Hypomnesis.Core.Eval

/-!
# Sûreté du typage : « well-typed programs don't go wrong »

On type les valeurs runtime (`ValTy`) — une fermeture est bien typée si son
environnement capturé l'est et si son corps est bien typé dans le contexte
correspondant — puis on montre que l'évaluation d'un terme bien typé dans un
environnement bien typé ne rend jamais `stuck`, quel que soit le budget. Un
échec de filtrage (`matchFail`) reste possible : c'est l'objet de HYP-022.
-/

namespace Hypomnesis.Core

mutual
  inductive ValTy (sig : Sig) : Val → Ty → Prop where
    | int {n} : ValTy sig (.int n) .int
    | bool {b} : ValTy sig (.bool b) .bool
    | float {f} : ValTy sig (.float f) .float
    | string {s} : ValTy sig (.string s) .string
    | unit : ValTy sig .unit .unit
    | clo {env Γ t₁ t₂ b} :
        EnvTy sig env Γ → HasType sig (t₁ :: Γ) b t₂ → ValTy sig (.clo env b) (.arrow t₁ t₂)
    | rclo {env Γ t₁ t₂ b} :
        EnvTy sig env Γ → HasType sig (t₁ :: .arrow t₁ t₂ :: Γ) b t₂ →
        ValTy sig (.rclo env b) (.arrow t₁ t₂)
    | pair {a b t₁ t₂} :
        ValTy sig a t₁ → ValTy sig b t₂ → ValTy sig (.pair a b) (.prod t₁ t₂)
    | con {d c cs ta v} :
        sig[d]? = some cs → cs[c]? = some ta → ValTy sig v ta → ValTy sig (.con c v) (.data d)

  inductive EnvTy (sig : Sig) : List Val → Ctx → Prop where
    | nil : EnvTy sig [] []
    | cons {v t env Γ} : ValTy sig v t → EnvTy sig env Γ → EnvTy sig (v :: env) (t :: Γ)
end

/-- Un résultat est sûr à un type donné : valeur de ce type, budget épuisé, ou
échec de filtrage ou erreur explicite de primitive. Seul `stuck` est exclu. -/
def Safe (sig : Sig) : Res → Ty → Prop
  | .ok v, t => ValTy sig v t
  | .timeout, _ => True
  | .matchFail, _ => True
  | .error _, _ => True
  | .stuck, _ => False

variable {sig : Sig}

theorem EnvTy.lookup {env : List Val} :
    ∀ {Γ : Ctx}, EnvTy sig env Γ →
      ∀ {i : Nat} {t : Ty}, Γ[i]? = some t → ∃ v, env[i]? = some v ∧ ValTy sig v t := by
  induction env with
  | nil => intro Γ h i t hi; cases h; simp at hi
  | cons v env ih =>
    intro Γ h i t hi
    cases h with
    | cons hv henv =>
      cases i with
      | zero => simp at hi; subst hi; exact ⟨_, rfl, hv⟩
      | succ i => simpa using ih henv (by simpa using hi)

theorem EnvTy.append {vs : List Val} :
    ∀ {bs : Ctx} {env : List Val} {Γ : Ctx},
      EnvTy sig vs bs → EnvTy sig env Γ → EnvTy sig (vs ++ env) (bs ++ Γ) := by
  induction vs with
  | nil => intro bs env Γ h henv; cases h; exact henv
  | cons v vs ih =>
    intro bs env Γ h henv
    cases h with
    | cons hv hvs => exact EnvTy.cons hv (ih hvs henv)

/-- **Filtrage bien typé** : si un motif de type `t` filtre une valeur de type `t`,
les valeurs liées ont les types annoncés par le motif. -/
theorem matchPat_sound {p : Pat} {t : Ty} {bs : Ctx} (hp : PatTy sig p t bs) :
    ∀ {v : Val} {vs : List Val}, ValTy sig v t → matchPat p v = some vs → EnvTy sig vs bs := by
  induction hp with
  | wild => intro v vs _ h; simp [matchPat] at h; subst h; exact EnvTy.nil
  | var => intro v vs hv h; simp [matchPat] at h; subst h; exact EnvTy.cons hv EnvTy.nil
  | int =>
    intro v vs hv h
    cases hv
    simp only [matchPat] at h
    split at h <;> simp at h
    subst h; exact EnvTy.nil
  | bool =>
    intro v vs hv h
    cases hv
    simp only [matchPat] at h
    split at h <;> simp at h
    subst h; exact EnvTy.nil
  | float =>
    intro v vs hv h
    cases hv
    simp only [matchPat] at h
    split at h <;> simp at h
    subst h; exact EnvTy.nil
  | string =>
    intro v vs hv h
    cases hv
    simp only [matchPat] at h
    split at h <;> simp at h
    subst h; exact EnvTy.nil
  | pair _ _ ih₁ ih₂ =>
    intro v vs hv h
    cases hv with
    | pair ha hb =>
      simp only [matchPat] at h
      split at h
      · rename_i vs₁ vs₂ h₁ h₂
        simp at h; subst h
        exact EnvTy.append (ih₂ hb h₂) (ih₁ ha h₁)
      · simp at h
  | ctor hd hc _ ih =>
    intro v vs hv h
    cases hv with
    | con hd' hc' hv' =>
      simp only [matchPat] at h
      split at h
      · rename_i heq
        subst heq
        rw [hd] at hd'
        cases hd'
        rw [hc] at hc'
        cases hc'
        exact ih hv' h
      · simp at h

theorem Safe.bind {r : Res} {k : Val → Res} {t₁ t₂ : Ty}
    (hr : Safe sig r t₁) (hk : ∀ v, ValTy sig v t₁ → Safe sig (k v) t₂) :
    Safe sig (r.bind k) t₂ := by
  cases r with
  | ok v => exact hk v hr
  | stuck => exact absurd hr id
  | timeout => trivial
  | matchFail => trivial
  | error => trivial

theorem evalOp_ty (op : BinOp) {a b : Val}
    (ha : ValTy sig a op.domain) (hb : ValTy sig b op.domain) :
    Safe sig (evalOp op a b) op.result := by
  cases op <;> cases ha <;> cases hb <;> simp only [evalOp] <;> first
    | exact ValTy.int
    | exact ValTy.bool
    | exact ValTy.float
    | exact ValTy.string
    | split <;> first | trivial | exact ValTy.int

/-- **Sûreté.** Pour tout budget, un terme bien typé évalué dans un
environnement bien typé ne se bloque pas, et toute valeur produite a le type
annoncé. -/
theorem eval_safe (n : Nat) :
    ∀ {env : List Val} {Γ : Ctx} {e : Expr} {t : Ty},
      EnvTy sig env Γ → HasType sig Γ e t → Safe sig (eval n env e) t := by
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
    | float => exact ValTy.float
    | string => exact ValTy.string
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
      exact evalOp_ty _ hva hvb
    | construct hd hc he =>
      exact Safe.bind (ih henv he) fun v hv => ValTy.con hd hc hv
    | case hx hp h₁ h₂ =>
      refine Safe.bind (ih henv hx) fun v hv => ?_
      show Safe sig (match matchPat _ v with
        | some vs => eval n (vs ++ env) _
        | none => eval n env _) _
      split
      · rename_i vs hm
        exact ih (EnvTy.append (matchPat_sound hp hv hm) henv) h₁
      · exact ih henv h₂
    | fail => trivial
    | raise hm =>
      refine Safe.bind (ih henv hm) fun v hv => ?_
      cases hv
      trivial

/-- Corollaire pour un programme clos : jamais `stuck`. -/
theorem closed_never_stuck {e : Expr} {t : Ty} (h : HasType sig [] e t) (n : Nat) :
    eval n [] e ≠ .stuck := by
  intro hstuck
  have hs := eval_safe n EnvTy.nil h
  rw [hstuck] at hs
  exact hs

end Hypomnesis.Core
