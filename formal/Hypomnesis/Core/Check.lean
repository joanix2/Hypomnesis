import Hypomnesis.Core.Typing

/-!
# Vérificateur de types exécutable, correct et complet

`typeOf` est le vérificateur de certificats : le compilateur Python élabore
un programme (inférence Hindley-Milner, résolution des noms) puis exporte un
terme annoté ; `typeOf` le revérifie. Les théorèmes ci-dessous établissent
que `typeOf` décide exactement la relation `HasType` : on n'a donc à faire
confiance ni à l'inférence Python, ni à l'export, seulement à ce noyau.
-/

namespace Hypomnesis.Core

/-- Types des variables liées par un motif filtrant des valeurs de type `t`. -/
def patTypeOf (sig : Sig) : Pat → Ty → Option Ctx
  | .wild, _ => some []
  | .var, t => some [t]
  | .int _, .int => some []
  | .bool _, .bool => some []
  | .pair p₁ p₂, .prod t₁ t₂ =>
    match patTypeOf sig p₁ t₁, patTypeOf sig p₂ t₂ with
    | some b₁, some b₂ => some (b₂ ++ b₁)
    | _, _ => none
  | .ctor c p, .data d =>
    match sig[d]? with
    | some cs =>
      match cs[c]? with
      | some ta => patTypeOf sig p ta
      | none => none
    | none => none
  | _, _ => none

def typeOf (sig : Sig) (Γ : Ctx) : Expr → Option Ty
  | .var i => Γ[i]?
  | .int _ => some .int
  | .bool _ => some .bool
  | .unit => some .unit
  | .lam t b => (typeOf sig (t :: Γ) b).map (.arrow t)
  | .fix t₁ t₂ b =>
    match typeOf sig (t₁ :: .arrow t₁ t₂ :: Γ) b with
    | some r => if r = t₂ then some (.arrow t₁ t₂) else none
    | none => none
  | .app f a =>
    match typeOf sig Γ f, typeOf sig Γ a with
    | some (.arrow t₁ t₂), some ta => if t₁ = ta then some t₂ else none
    | _, _ => none
  | .letE x b =>
    match typeOf sig Γ x with
    | some tx => typeOf sig (tx :: Γ) b
    | none => none
  | .ite c a b =>
    match typeOf sig Γ c, typeOf sig Γ a, typeOf sig Γ b with
    | some .bool, some ta, some tb => if ta = tb then some ta else none
    | _, _, _ => none
  | .pair a b =>
    match typeOf sig Γ a, typeOf sig Γ b with
    | some ta, some tb => some (.prod ta tb)
    | _, _ => none
  | .fst x =>
    match typeOf sig Γ x with
    | some (.prod t₁ _) => some t₁
    | _ => none
  | .snd x =>
    match typeOf sig Γ x with
    | some (.prod _ t₂) => some t₂
    | _ => none
  | .binop op a b =>
    match typeOf sig Γ a, typeOf sig Γ b with
    | some .int, some .int => some op.result
    | _, _ => none
  | .construct d c x =>
    match sig[d]? with
    | some cs =>
      match cs[c]?, typeOf sig Γ x with
      | some ta, some tx => if ta = tx then some (.data d) else none
      | _, _ => none
    | none => none
  | .case x p e₁ e₂ =>
    match typeOf sig Γ x with
    | some tx =>
      match patTypeOf sig p tx with
      | some bs =>
        match typeOf sig (bs ++ Γ) e₁, typeOf sig Γ e₂ with
        | some t₁, some t₂ => if t₁ = t₂ then some t₁ else none
        | _, _ => none
      | none => none
    | none => none
  | .fail t => some t

variable {sig : Sig}

theorem patTypeOf_sound {p : Pat} {t : Ty} {bs : Ctx} (h : patTypeOf sig p t = some bs) :
    PatTy sig p t bs := by
  induction p generalizing t bs with
  | wild => simp [patTypeOf] at h; subst h; exact .wild
  | var => simp [patTypeOf] at h; subst h; exact .var
  | int n =>
    cases t <;> simp [patTypeOf] at h
    subst h; exact .int
  | bool b =>
    cases t <;> simp [patTypeOf] at h
    subst h; exact .bool
  | pair p₁ p₂ ih₁ ih₂ =>
    cases t with
    | prod t₁ t₂ =>
      simp only [patTypeOf] at h
      split at h
      · rename_i b₁ b₂ h₁ h₂
        simp at h; subst h
        exact .pair (ih₁ h₁) (ih₂ h₂)
      · simp at h
    | _ => simp [patTypeOf] at h
  | ctor c p ih =>
    cases t with
    | data d =>
      simp only [patTypeOf] at h
      split at h
      · rename_i cs hd
        split at h
        · rename_i ta hc
          exact .ctor hd hc (ih h)
        · simp at h
      · simp at h
    | _ => simp [patTypeOf] at h

theorem patTypeOf_complete {p : Pat} {t : Ty} {bs : Ctx} (h : PatTy sig p t bs) :
    patTypeOf sig p t = some bs := by
  induction h with
  | wild | var | int | bool => rfl
  | pair _ _ ih₁ ih₂ => simp [patTypeOf, ih₁, ih₂]
  | ctor hd hc _ ih => simp [patTypeOf, hd, hc, ih]

/-- **Correction** : un type rendu par `typeOf` est dérivable. -/
theorem typeOf_sound {Γ : Ctx} {e : Expr} {t : Ty} (h : typeOf sig Γ e = some t) :
    HasType sig Γ e t := by
  induction e generalizing Γ t with
  | var i => exact .var h
  | int => simp [typeOf] at h; subst h; exact .int
  | bool => simp [typeOf] at h; subst h; exact .bool
  | unit => simp [typeOf] at h; subst h; exact .unit
  | lam t₁ b ih =>
    simp only [typeOf, Option.map_eq_some_iff] at h
    obtain ⟨t₂, hb, rfl⟩ := h
    exact .lam (ih hb)
  | fix t₁ t₂ b ih =>
    simp only [typeOf] at h
    split at h
    · rename_i r hb
      split at h
      · rename_i hr
        subst hr
        simp at h
        subst h
        exact .fix (ih hb)
      · simp at h
    · simp at h
  | app f a ihf iha =>
    simp only [typeOf] at h
    split at h
    · rename_i t₁ t₂ ta hf ha
      split at h
      · rename_i heq
        subst heq
        simp at h
        subst h
        exact .app (ihf hf) (iha ha)
      · simp at h
    · simp at h
  | letE x b ihx ihb =>
    simp only [typeOf] at h
    split at h
    · rename_i tx hx
      exact .letE (ihx hx) (ihb h)
    · simp at h
  | ite c a b ihc iha ihb =>
    simp only [typeOf] at h
    split at h
    · rename_i ta tb hc ha hb
      split at h
      · rename_i heq
        subst heq
        simp at h
        subst h
        exact .ite (ihc hc) (iha ha) (ihb hb)
      · simp at h
    · simp at h
  | pair a b iha ihb =>
    simp only [typeOf] at h
    split at h
    · rename_i ta tb ha hb
      simp at h
      subst h
      exact .pair (iha ha) (ihb hb)
    · simp at h
  | fst x ih =>
    simp only [typeOf] at h
    split at h
    · rename_i t₁ t₂ hx
      simp at h
      subst h
      exact .fst (ih hx)
    · simp at h
  | snd x ih =>
    simp only [typeOf] at h
    split at h
    · rename_i t₁ t₂ hx
      simp at h
      subst h
      exact .snd (ih hx)
    · simp at h
  | binop op a b iha ihb =>
    simp only [typeOf] at h
    split at h
    · rename_i ha hb
      simp at h
      subst h
      exact .binop (iha ha) (ihb hb)
    · simp at h
  | construct d c x ih =>
    simp only [typeOf] at h
    split at h
    · rename_i cs hd
      split at h
      · rename_i ta tx hc hx
        split at h
        · rename_i heq
          subst heq
          simp at h
          subst h
          exact .construct hd hc (ih hx)
        · simp at h
      · simp at h
    · simp at h
  | case x p e₁ e₂ ihx ih₁ ih₂ =>
    simp only [typeOf] at h
    split at h
    · rename_i tx hx
      split at h
      · rename_i bs hp
        split at h
        · rename_i t₁ t₂ h₁ h₂
          split at h
          · rename_i heq
            subst heq
            simp at h
            subst h
            exact .case (ihx hx) (patTypeOf_sound hp) (ih₁ h₁) (ih₂ h₂)
          · simp at h
        · simp at h
      · simp at h
    · simp at h
  | fail t' => simp [typeOf] at h; subst h; exact .fail

/-- **Complétude** : tout jugement dérivable est trouvé par `typeOf`. -/
theorem typeOf_complete {Γ : Ctx} {e : Expr} {t : Ty} (h : HasType sig Γ e t) :
    typeOf sig Γ e = some t := by
  induction h with
  | var h => exact h
  | int | bool | unit | fail => rfl
  | lam _ ih => simp [typeOf, ih]
  | fix _ ih => simp [typeOf, ih]
  | app _ _ ihf iha => simp [typeOf, ihf, iha]
  | letE _ _ ihx ihb => simp [typeOf, ihx, ihb]
  | ite _ _ _ ihc iha ihb => simp [typeOf, ihc, iha, ihb]
  | pair _ _ iha ihb => simp [typeOf, iha, ihb]
  | fst _ ih => simp [typeOf, ih]
  | snd _ ih => simp [typeOf, ih]
  | binop _ _ iha ihb => simp [typeOf, iha, ihb]
  | construct hd hc _ ih => simp [typeOf, hd, hc, ih]
  | case _ hp _ _ ihx ih₁ ih₂ => simp [typeOf, ihx, patTypeOf_complete hp, ih₁, ih₂]

/-- Le typage du fragment est décidable. -/
theorem hasType_iff_typeOf {Γ : Ctx} {e : Expr} {t : Ty} :
    HasType sig Γ e t ↔ typeOf sig Γ e = some t :=
  ⟨typeOf_complete, typeOf_sound⟩

instance (sig : Sig) (Γ : Ctx) (e : Expr) (t : Ty) : Decidable (HasType sig Γ e t) :=
  decidable_of_iff _ hasType_iff_typeOf.symm

/-- Unicité des types : un terme annoté a au plus un type. -/
theorem hasType_unique {Γ : Ctx} {e : Expr} {t₁ t₂ : Ty}
    (h₁ : HasType sig Γ e t₁) (h₂ : HasType sig Γ e t₂) : t₁ = t₂ := by
  have := (typeOf_complete h₁).symm.trans (typeOf_complete h₂)
  exact Option.some.inj this

end Hypomnesis.Core
