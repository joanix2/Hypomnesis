import Hypomnesis.Core.Check
import Hypomnesis.Core.Soundness

/-!
# Records nominaux comme formes dérivées (HYP-021)

Une instance `d` de Σ a un constructeur unique ; son argument est un produit
de champs terminé par unit. Deux noms de records occupent deux indices
distincts, même si leurs champs ont les mêmes types. Les opérations ci-dessous
ne modifient ni `typeOf` ni `eval` : leurs preuves s'appliquent aux formes dérivées.
-/

namespace Hypomnesis.Core.Records

def payloadTy : List Ty → Ty
  | [] => .unit
  | t :: ts => .prod t (payloadTy ts)

def payload : List Expr → Expr
  | [] => .unit
  | e :: es => .pair e (payload es)

def project (i : Nat) (e : Expr) : Expr :=
  match i with
  | 0 => .fst e
  | n + 1 => project n (.snd e)

def replaceAt : List Ty → Nat → Expr → Expr → Expr
  | [], _, _, _ => .unit
  | _ :: _, 0, e, value => .pair value (.snd e)
  | _ :: ts, n + 1, e, value => .pair (.fst e) (replaceAt ts n (.snd e) value)

def make (d : Nat) (values : List Expr) : Expr :=
  .construct d 0 (payload values)

def get (d i : Nat) (t : Ty) : Expr :=
  .lam (.data d) (.case (.var 0) (.ctor 0 .var) (project i (.var 0)) (.fail t))

def update (d i : Nat) (fields : List Ty) (t : Ty) : Expr :=
  .lam t (.lam (.data d)
    (.case (.var 0) (.ctor 0 .var)
      (.construct d 0 (replaceAt fields i (.var 0) (.var 2)))
      (.fail (.data d))))

inductive FieldsTyped (sig : Sig) (Γ : Ctx) : List Expr → List Ty → Prop where
  | nil : FieldsTyped sig Γ [] []
  | cons {e es t ts} :
      HasType sig Γ e t → FieldsTyped sig Γ es ts → FieldsTyped sig Γ (e :: es) (t :: ts)

theorem payload_typed {sig : Sig} {Γ : Ctx} {es : List Expr} {ts : List Ty}
    (h : FieldsTyped sig Γ es ts) :
    HasType sig Γ (payload es) (payloadTy ts) := by
  induction h with
  | nil => exact .unit
  | cons h _ ih => exact .pair h ih

theorem project_typed {sig : Sig} {Γ : Ctx} {fields : List Ty} {e : Expr} {i : Nat} {t : Ty}
    (he : HasType sig Γ e (payloadTy fields)) (hi : fields[i]? = some t) :
    HasType sig Γ (project i e) t := by
  induction i generalizing fields e with
  | zero =>
    cases fields with
    | nil => simp at hi
    | cons a rest =>
      simp at hi
      subst t
      exact .fst he
  | succ n ih =>
    cases fields with
    | nil => simp at hi
    | cons a rest =>
      exact ih (.snd he) (by simpa using hi)

theorem replaceAt_typed {sig : Sig} {Γ : Ctx} {fields : List Ty}
    {e value : Expr} {i : Nat} {t : Ty}
    (he : HasType sig Γ e (payloadTy fields)) (hv : HasType sig Γ value t)
    (hi : fields[i]? = some t) :
    HasType sig Γ (replaceAt fields i e value) (payloadTy fields) := by
  induction fields generalizing i e with
  | nil => simp at hi
  | cons a rest ih =>
    cases i with
    | zero =>
      simp at hi
      subst t
      exact .pair hv (.snd he)
    | succ n =>
      exact .pair (.fst he) (ih (.snd he) (by simpa using hi))

theorem make_typed {sig : Sig} {Γ : Ctx} {d : Nat} {fields : List Ty} {es : List Expr}
    (hd : sig[d]? = some [payloadTy fields])
    (hs : FieldsTyped sig Γ es fields) :
    HasType sig Γ (make d es) (.data d) :=
  .construct hd rfl (payload_typed hs)

theorem get_typed {sig : Sig} {Γ : Ctx} {d i : Nat} {fields : List Ty} {t : Ty}
    (hd : sig[d]? = some [payloadTy fields]) (hi : fields[i]? = some t) :
    HasType sig Γ (get d i t) (.arrow (.data d) t) := by
  apply HasType.lam
  apply HasType.case (tx := .data d) (bs := [payloadTy fields])
  · exact .var rfl
  · exact .ctor hd rfl .var
  · exact project_typed (.var rfl) hi
  · exact .fail

theorem update_typed {sig : Sig} {Γ : Ctx} {d i : Nat} {fields : List Ty} {t : Ty}
    (hd : sig[d]? = some [payloadTy fields]) (hi : fields[i]? = some t) :
    HasType sig Γ (update d i fields t) (.arrow t (.arrow (.data d) (.data d))) := by
  apply HasType.lam
  apply HasType.lam
  apply HasType.case (tx := .data d) (bs := [payloadTy fields])
  · exact .var rfl
  · exact .ctor hd rfl .var
  · exact .construct hd rfl (replaceAt_typed (.var rfl) (.var rfl) hi)
  · exact .fail

theorem update_checked {sig : Sig} {Γ : Ctx} {d i : Nat} {fields : List Ty} {t : Ty}
    (hd : sig[d]? = some [payloadTy fields]) (hi : fields[i]? = some t) :
    typeOf sig Γ (update d i fields t) = some (.arrow t (.arrow (.data d) (.data d))) :=
  typeOf_complete (update_typed hd hi)

theorem update_never_stuck {sig : Sig} {d i : Nat} {fields : List Ty} {t : Ty}
    {value record : Expr}
    (hd : sig[d]? = some [payloadTy fields]) (hi : fields[i]? = some t)
    (hv : HasType sig [] value t) (hr : HasType sig [] record (.data d)) (fuel : Nat) :
    eval fuel [] (.app (.app (update d i fields t) value) record) ≠ .stuck :=
  closed_never_stuck (.app (.app (update_typed hd hi) hv) hr) fuel

theorem get_never_stuck {sig : Sig} {d i : Nat} {fields : List Ty} {t : Ty} {record : Expr}
    (hd : sig[d]? = some [payloadTy fields]) (hi : fields[i]? = some t)
    (hr : HasType sig [] record (.data d)) (fuel : Nat) :
    eval fuel [] (.app (get d i t) record) ≠ .stuck :=
  closed_never_stuck (.app (get_typed hd hi) hr) fuel

end Hypomnesis.Core.Records
