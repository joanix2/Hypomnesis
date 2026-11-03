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

def typeOf (Γ : Ctx) : Expr → Option Ty
  | .var i => Γ[i]?
  | .int _ => some .int
  | .bool _ => some .bool
  | .unit => some .unit
  | .lam t b => (typeOf (t :: Γ) b).map (.arrow t)
  | .fix t₁ t₂ b =>
    match typeOf (t₁ :: .arrow t₁ t₂ :: Γ) b with
    | some r => if r = t₂ then some (.arrow t₁ t₂) else none
    | none => none
  | .app f a =>
    match typeOf Γ f, typeOf Γ a with
    | some (.arrow t₁ t₂), some ta => if t₁ = ta then some t₂ else none
    | _, _ => none
  | .letE x b =>
    match typeOf Γ x with
    | some tx => typeOf (tx :: Γ) b
    | none => none
  | .ite c a b =>
    match typeOf Γ c, typeOf Γ a, typeOf Γ b with
    | some .bool, some ta, some tb => if ta = tb then some ta else none
    | _, _, _ => none
  | .pair a b =>
    match typeOf Γ a, typeOf Γ b with
    | some ta, some tb => some (.prod ta tb)
    | _, _ => none
  | .fst x =>
    match typeOf Γ x with
    | some (.prod t₁ _) => some t₁
    | _ => none
  | .snd x =>
    match typeOf Γ x with
    | some (.prod _ t₂) => some t₂
    | _ => none
  | .binop op a b =>
    match typeOf Γ a, typeOf Γ b with
    | some .int, some .int => some op.result
    | _, _ => none

/-- **Correction** : un type rendu par `typeOf` est dérivable. -/
theorem typeOf_sound {Γ : Ctx} {e : Expr} {t : Ty} (h : typeOf Γ e = some t) :
    HasType Γ e t := by
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

/-- **Complétude** : tout jugement dérivable est trouvé par `typeOf`. -/
theorem typeOf_complete {Γ : Ctx} {e : Expr} {t : Ty} (h : HasType Γ e t) :
    typeOf Γ e = some t := by
  induction h with
  | var h => exact h
  | int | bool | unit => rfl
  | lam _ ih => simp [typeOf, ih]
  | fix _ ih => simp [typeOf, ih]
  | app _ _ ihf iha => simp [typeOf, ihf, iha]
  | letE _ _ ihx ihb => simp [typeOf, ihx, ihb]
  | ite _ _ _ ihc iha ihb => simp [typeOf, ihc, iha, ihb]
  | pair _ _ iha ihb => simp [typeOf, iha, ihb]
  | fst _ ih => simp [typeOf, ih]
  | snd _ ih => simp [typeOf, ih]
  | binop _ _ iha ihb => simp [typeOf, iha, ihb]

/-- Le typage du fragment est décidable. -/
theorem hasType_iff_typeOf {Γ : Ctx} {e : Expr} {t : Ty} :
    HasType Γ e t ↔ typeOf Γ e = some t :=
  ⟨typeOf_complete, typeOf_sound⟩

instance (Γ : Ctx) (e : Expr) (t : Ty) : Decidable (HasType Γ e t) :=
  decidable_of_iff _ hasType_iff_typeOf.symm

/-- Unicité des types : un terme annoté a au plus un type. -/
theorem hasType_unique {Γ : Ctx} {e : Expr} {t₁ t₂ : Ty}
    (h₁ : HasType Γ e t₁) (h₂ : HasType Γ e t₂) : t₁ = t₂ := by
  have := (typeOf_complete h₁).symm.trans (typeOf_complete h₂)
  exact Option.some.inj this

end Hypomnesis.Core
