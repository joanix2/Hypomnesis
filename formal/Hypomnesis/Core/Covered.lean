import Hypomnesis.Core.Coverage

/-!
# Programmes à filtrages certifiés

`Certified` renforce le typage déclaratif : pas de `fail` isolé, et chaque
groupe de filtrage se termine par un certificat de couverture calculé.
Les fermetures et fonctions récursives conservent cette propriété.
Les `case` intermédiaires sont aussi permis si leurs deux branches sont sûres.
-/

namespace Hypomnesis.Core.Coverage

inductive Certified (sig : Sig) : Ctx → Expr → Ty → Prop where
  | var {Γ i t} : Γ[i]? = some t → Certified sig Γ (.var i) t
  | int {Γ n} : Certified sig Γ (.int n) .int
  | bool {Γ b} : Certified sig Γ (.bool b) .bool
  | float {Γ f} : Certified sig Γ (.float f) .float
  | string {Γ s} : Certified sig Γ (.string s) .string
  | unit {Γ} : Certified sig Γ .unit .unit
  | lam {Γ a b body} :
      Certified sig (a :: Γ) body b → Certified sig Γ (.lam a body) (.arrow a b)
  | fix {Γ a b body} :
      Certified sig (a :: .arrow a b :: Γ) body b →
      Certified sig Γ (.fix a b body) (.arrow a b)
  | app {Γ f x a b} :
      Certified sig Γ f (.arrow a b) → Certified sig Γ x a →
      Certified sig Γ (.app f x) b
  | letE {Γ x body a b} :
      Certified sig Γ x a → Certified sig (a :: Γ) body b →
      Certified sig Γ (.letE x body) b
  | ite {Γ c a b t} :
      Certified sig Γ c .bool → Certified sig Γ a t → Certified sig Γ b t →
      Certified sig Γ (.ite c a b) t
  | pair {Γ a b ta tb} :
      Certified sig Γ a ta → Certified sig Γ b tb →
      Certified sig Γ (.pair a b) (.prod ta tb)
  | fst {Γ e a b} : Certified sig Γ e (.prod a b) → Certified sig Γ (.fst e) a
  | snd {Γ e a b} : Certified sig Γ e (.prod a b) → Certified sig Γ (.snd e) b
  | binop {Γ op a b} :
      Certified sig Γ a op.domain → Certified sig Γ b op.domain →
      Certified sig Γ (.binop op a b) op.result
  | construct {Γ d c cs ta e} :
      sig[d]? = some cs → cs[c]? = some ta → Certified sig Γ e ta →
      Certified sig Γ (.construct d c e) (.data d)
  | case {Γ x p a b tx bs t} :
      Certified sig Γ x tx → PatTy sig p tx bs →
      Certified sig (bs ++ Γ) a t → Certified sig Γ b t →
      Certified sig Γ (.case x p a b) t
  | raise {Γ t message} :
      Certified sig Γ message .string → Certified sig Γ (.raise t message) t
  | casesE {Γ index tx t fuel arms} (bindings : (Pat × Expr) → Ctx) :
      Γ[index]? = some tx →
      exhaustive sig fuel tx (arms.map Prod.fst) = some true →
      (∀ arm ∈ arms, PatTy sig arm.1 tx (bindings arm)) →
      (∀ arm ∈ arms, Certified sig (bindings arm ++ Γ) arm.2 t) →
      Certified sig Γ (caseChain index t arms) t
  | matchE {Γ x tx t fuel arms} (bindings : (Pat × Expr) → Ctx) :
      Certified sig Γ x tx →
      exhaustive sig fuel tx (arms.map Prod.fst) = some true →
      (∀ arm ∈ arms, PatTy sig arm.1 tx (bindings arm)) →
      (∀ arm ∈ arms, Certified sig (bindings arm ++ tx :: Γ) arm.2 t) →
      Certified sig Γ (.letE x (caseChain 0 t arms)) t

theorem caseChain_typed {sig : Sig} {Γ : Ctx} {index : Nat} {tx t : Ty}
    {arms : List (Pat × Expr)} (hx : Γ[index]? = some tx)
    (hb : ∀ arm ∈ arms, ∃ bs, PatTy sig arm.1 tx bs ∧ HasType sig (bs ++ Γ) arm.2 t) :
    HasType sig Γ (caseChain index t arms) t := by
  induction arms with
  | nil => exact .fail
  | cons arm rest ih =>
    obtain ⟨bs, hp, body⟩ := hb arm (by simp)
    exact .case (.var hx) hp body (ih fun a ha => hb a (List.mem_cons_of_mem _ ha))

theorem Certified.typed {sig : Sig} {Γ : Ctx} {e : Expr} {t : Ty}
    (h : Certified sig Γ e t) : HasType sig Γ e t := by
  induction h with
  | var h => exact .var h
  | int => exact .int
  | bool => exact .bool
  | float => exact .float
  | string => exact .string
  | unit => exact .unit
  | lam _ ih => exact .lam ih
  | fix _ ih => exact .fix ih
  | app _ _ ih₁ ih₂ => exact .app ih₁ ih₂
  | letE _ _ ih₁ ih₂ => exact .letE ih₁ ih₂
  | ite _ _ _ ih₁ ih₂ ih₃ => exact .ite ih₁ ih₂ ih₃
  | pair _ _ ih₁ ih₂ => exact .pair ih₁ ih₂
  | fst _ ih => exact .fst ih
  | snd _ ih => exact .snd ih
  | binop _ _ ih₁ ih₂ => exact .binop ih₁ ih₂
  | construct hd hc _ ih => exact .construct hd hc ih
  | case _ hp _ _ ih₁ ih₂ ih₃ => exact .case ih₁ hp ih₂ ih₃
  | raise _ ih => exact .raise ih
  | casesE bindings lookup _ patterns _ ih =>
    exact caseChain_typed lookup fun arm member =>
      ⟨bindings arm, patterns arm member, ih arm member⟩
  | @matchE Γ x tx t fuel arms bindings _ _ patterns _ ihx ihb =>
    apply HasType.letE ihx
    apply caseChain_typed (tx := tx) (by simp)
    intro arm member
    exact ⟨bindings arm, patterns arm member, ihb arm member⟩

mutual
  inductive ProtectedVal (sig : Sig) : Val → Ty → Prop where
    | int {n} : ProtectedVal sig (.int n) .int
    | bool {b} : ProtectedVal sig (.bool b) .bool
    | float {f} : ProtectedVal sig (.float f) .float
    | string {s} : ProtectedVal sig (.string s) .string
    | unit : ProtectedVal sig .unit .unit
    | clo {env Γ a b body} :
        ProtectedEnv sig env Γ → Certified sig (a :: Γ) body b →
        ProtectedVal sig (.clo env body) (.arrow a b)
    | rclo {env Γ a b body} :
        ProtectedEnv sig env Γ → Certified sig (a :: .arrow a b :: Γ) body b →
        ProtectedVal sig (.rclo env body) (.arrow a b)
    | pair {a b ta tb} :
        ProtectedVal sig a ta → ProtectedVal sig b tb →
        ProtectedVal sig (.pair a b) (.prod ta tb)
    | con {d c cs ta v} :
        sig[d]? = some cs → cs[c]? = some ta → ProtectedVal sig v ta →
        ProtectedVal sig (.con c v) (.data d)

  inductive ProtectedEnv (sig : Sig) : List Val → Ctx → Prop where
    | nil : ProtectedEnv sig [] []
    | cons {v t vs ts} :
        ProtectedVal sig v t → ProtectedEnv sig vs ts → ProtectedEnv sig (v :: vs) (t :: ts)
end

mutual
  theorem ProtectedVal.typed {sig : Sig} {v : Val} {t : Ty}
      (h : ProtectedVal sig v t) : ValTy sig v t := by
    cases h with
    | int => exact .int
    | bool => exact .bool
    | float => exact .float
    | string => exact .string
    | unit => exact .unit
    | clo he hb => exact .clo he.typed hb.typed
    | rclo he hb => exact .rclo he.typed hb.typed
    | pair ha hb => exact .pair ha.typed hb.typed
    | con hd hc hv => exact .con hd hc hv.typed

  theorem ProtectedEnv.typed {sig : Sig} {env : List Val} {Γ : Ctx}
      (h : ProtectedEnv sig env Γ) : EnvTy sig env Γ := by
    cases h with
    | nil => exact .nil
    | cons hv he => exact .cons hv.typed he.typed
end

theorem ProtectedEnv.lookup {sig : Sig} {env : List Val} {Γ : Ctx}
    (he : ProtectedEnv sig env Γ) {i : Nat} {t : Ty} (hi : Γ[i]? = some t) :
    ∃ v, env[i]? = some v ∧ ProtectedVal sig v t := by
  induction env generalizing Γ i with
  | nil => cases he; simp at hi
  | cons v env ih =>
    cases he with
    | cons hv he =>
    cases i with
    | zero => simp at hi; subst hi; exact ⟨_, rfl, hv⟩
    | succ i => exact ih he (by simpa using hi)

theorem ProtectedEnv.append {sig : Sig} {xs ys : List Val} {a b : Ctx}
    (hx : ProtectedEnv sig xs a) (hy : ProtectedEnv sig ys b) :
    ProtectedEnv sig (xs ++ ys) (a ++ b) := by
  induction xs generalizing a with
  | nil => cases hx; exact hy
  | cons v xs ih =>
    cases hx with
    | cons hv hx => exact .cons hv (ih hx)

theorem matchPat_protected {sig : Sig} {p : Pat} {t : Ty} {bs : Ctx}
    (hp : PatTy sig p t bs) {v : Val} {vs : List Val}
    (hv : ProtectedVal sig v t) (hm : matchPat p v = some vs) :
    ProtectedEnv sig vs bs := by
  induction hp generalizing v vs with
  | wild => simp [matchPat] at hm; subst hm; exact .nil
  | var => simp [matchPat] at hm; subst hm; exact .cons hv .nil
  | int | bool | float | string =>
    cases hv
    simp only [matchPat] at hm
    split at hm <;> simp at hm
    subst hm
    exact .nil
  | pair _ _ ih₁ ih₂ =>
    cases hv with
    | pair ha hb =>
      simp only [matchPat] at hm
      split at hm
      · rename_i xs ys hx hy
        simp at hm
        subst hm
        exact (ih₂ hb hy).append (ih₁ ha hx)
      · simp at hm
  | ctor hd hc _ ih =>
    cases hv with
    | con hd' hc' hv =>
      simp only [matchPat] at hm
      split at hm
      · rename_i eq
        subst eq
        rw [hd] at hd'
        cases hd'
        rw [hc] at hc'
        cases hc'
        exact ih hv hm
      · simp at hm

def Protected (sig : Sig) : Res → Ty → Prop
  | .ok v, t => ProtectedVal sig v t
  | .timeout, _ | .error _, _ => True
  | .matchFail, _ | .stuck, _ => False

theorem Protected.bind {sig : Sig} {r : Res} {k : Val → Res} {a b : Ty}
    (hr : Protected sig r a)
    (hk : ∀ v, ProtectedVal sig v a → Protected sig (k v) b) :
    Protected sig (r.bind k) b := by
  cases r with
  | ok v => exact hk v hr
  | stuck | matchFail => contradiction
  | timeout | error => trivial

theorem protectedOp {sig : Sig} (op : BinOp) {a b : Val}
    (ha : ProtectedVal sig a op.domain) (hb : ProtectedVal sig b op.domain) :
    Protected sig (evalOp op a b) op.result := by
  cases op <;> cases ha <;> cases hb <;> simp only [evalOp] <;> first
    | exact ProtectedVal.int
    | exact ProtectedVal.bool
    | exact ProtectedVal.float
    | exact ProtectedVal.string
    | split <;> first | trivial | exact ProtectedVal.int

theorem caseChain_protected {sig : Sig} {budget index : Nat} {tx t : Ty}
    {env : List Val} {Γ : Ctx} {v : Val} {arms : List (Pat × Expr)}
    (he : ProtectedEnv sig env Γ) (lookup : env[index]? = some v)
    (hv : ProtectedVal sig v tx)
    (covered : ∃ p ∈ arms.map Prod.fst, ∃ bs, matchPat p v = some bs)
    (bodies : ∀ arm ∈ arms, ∃ bs, PatTy sig arm.1 tx bs ∧
      ∀ n < budget, ∀ {values}, ProtectedEnv sig values (bs ++ Γ) →
        Protected sig (eval n values arm.2) t) :
    Protected sig (eval budget env (caseChain index t arms)) t := by
  induction budget generalizing arms with
  | zero => trivial
  | succ budget ih =>
    cases arms with
    | nil => simp at covered
    | cons arm rest =>
      cases budget with
      | zero => trivial
      | succ budget =>
        simp only [caseChain, eval, lookup, Res.bind]
        cases hm : matchPat arm.1 v with
        | some values =>
          obtain ⟨bs, hp, safe⟩ := bodies arm (by simp)
          exact safe (budget + 1) (by omega) ((matchPat_protected hp hv hm).append he)
        | none =>
          apply ih
          · obtain ⟨p, member, bs, matched⟩ := covered
            rcases List.mem_cons.mp member with hp | member
            · simp [hp, hm] at matched
            · exact ⟨p, member, bs, matched⟩
          · intro a ha
            obtain ⟨bs, hp, safe⟩ := bodies a (List.mem_cons_of_mem _ ha)
            exact ⟨bs, hp, fun n hn => safe n (by omega)⟩

theorem eval_protected {sig : Sig} (fuel : Nat) :
    ∀ {env Γ e t}, ProtectedEnv sig env Γ → Certified sig Γ e t →
      Protected sig (eval fuel env e) t := by
  induction fuel using Nat.strongRecOn with
  | ind fuel ih =>
    intro env Γ e t he hc
    cases fuel with
    | zero => trivial
    | succ n =>
      have step : ∀ {env Γ e t}, ProtectedEnv sig env Γ → Certified sig Γ e t →
          Protected sig (eval n env e) t := fun he hc => ih n (by omega) he hc
      cases hc with
      | var h =>
        obtain ⟨v, hv, ht⟩ := he.lookup h
        simpa [eval, hv, Protected] using ht
      | int => exact .int
      | bool => exact .bool
      | float => exact .float
      | string => exact .string
      | unit => exact .unit
      | lam body => exact .clo he body
      | fix body => exact .rclo he body
      | app hf ha =>
        refine Protected.bind (step he hf) fun fv hfv =>
          Protected.bind (step he ha) fun av hav => ?_
        cases hfv with
        | clo he hb => exact step (.cons hav he) hb
        | rclo he hb => exact step (.cons hav (.cons (.rclo he hb) he)) hb
      | letE hx hb =>
        exact Protected.bind (step he hx) fun v hv => step (.cons hv he) hb
      | ite hc ha hb =>
        refine Protected.bind (step he hc) fun cv hcv => ?_
        cases hcv with
        | @bool b =>
          cases b
          · exact step he hb
          · exact step he ha
      | pair ha hb =>
        exact Protected.bind (step he ha) fun va hva =>
          Protected.bind (step he hb) fun vb hvb => ProtectedVal.pair hva hvb
      | fst hx =>
        refine Protected.bind (step he hx) fun v hv => ?_
        cases hv with
        | pair ha _ => exact ha
      | snd hx =>
        refine Protected.bind (step he hx) fun v hv => ?_
        cases hv with
        | pair _ hb => exact hb
      | binop ha hb =>
        exact Protected.bind (step he ha) fun va hva =>
          Protected.bind (step he hb) fun vb hvb => protectedOp _ hva hvb
      | construct hd hc hx =>
        exact Protected.bind (step he hx) fun v hv => ProtectedVal.con hd hc hv
      | case hx hp ha hb =>
        refine Protected.bind (step he hx) fun v hv => ?_
        show Protected sig (match matchPat _ v with
          | some vs => eval n (vs ++ env) _
          | none => eval n env _) _
        split
        · rename_i vs hm
          exact step ((matchPat_protected hp hv hm).append he) ha
        · exact step he hb
      | raise hm =>
        refine Protected.bind (step he hm) fun v hv => ?_
        cases hv
        trivial
      | casesE bindings lookup covered patterns bodies =>
        obtain ⟨v, lookup, hv⟩ := he.lookup lookup
        apply caseChain_protected he lookup hv (exhaustive_sound covered hv.typed)
        intro arm member
        exact ⟨bindings arm, patterns arm member,
          fun m hm _ henv => ih m (by omega) henv (bodies arm member)⟩
      | @matchE _ x tx t budget arms bindings hx covered patterns bodies =>
        refine Protected.bind (step he hx) fun v hv => ?_
        apply caseChain_protected (.cons hv he) (by simp) hv (exhaustive_sound covered hv.typed)
        intro arm member
        exact ⟨bindings arm, patterns arm member,
          fun m hm _ henv => ih m (by omega) henv (bodies arm member)⟩

theorem certified_program_no_matchFail {sig : Sig} {e : Expr} {t : Ty}
    (h : Certified sig [] e t) (fuel : Nat) : eval fuel [] e ≠ .matchFail := by
  intro failed
  have safe := eval_protected fuel ProtectedEnv.nil h
  rw [failed] at safe
  exact safe

end Hypomnesis.Core.Coverage
