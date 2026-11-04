import Hypomnesis.Core.Eval

/-!
# Adéquation des budgets

Le §11 du cahier des charges impose des budgets de calcul. On montre qu'un
budget n'influe que sur l'arrêt : dès qu'un budget suffit à obtenir un
résultat (valeur ou erreur), tout budget plus grand donne le même résultat.
Couplé au déterminisme (`eval` est une fonction), le résultat d'un programme
est donc bien défini indépendamment du budget choisi.
-/

namespace Hypomnesis.Core

theorem Res.bind_mono {r r' : Res} {k k' : Val → Res}
    (hr : r ≠ .timeout → r' = r) (hk : ∀ v, k v ≠ .timeout → k' v = k v) :
    r.bind k ≠ .timeout → r'.bind k' = r.bind k := by
  intro h
  cases r with
  | ok v =>
    rw [hr (by simp)]
    exact hk v h
  | stuck => rw [hr (by simp)]; rfl
  | matchFail => rw [hr (by simp)]; rfl
  | error => rw [hr (by simp)]; rfl
  | timeout => exact absurd rfl h

theorem eval_succ (n : Nat) :
    ∀ {env : List Val} {e : Expr},
      eval n env e ≠ .timeout → eval (n + 1) env e = eval n env e := by
  induction n with
  | zero => intro env e h; exact absurd rfl h
  | succ n ih =>
    intro env e h
    cases e with
    | var | int | bool | float | string | unit | lam | fix => rfl
    | app f a =>
      refine Res.bind_mono ih (fun fv => Res.bind_mono ih (fun av hk => ?_)) h
      cases fv <;> first | rfl | exact ih hk
    | letE x b => exact Res.bind_mono ih (fun _ hk => ih hk) h
    | ite c a b =>
      refine Res.bind_mono ih (fun cv hk => ?_) h
      cases cv with
      | bool b => cases b <;> exact ih hk
      | _ => rfl
    | pair a b => exact Res.bind_mono ih (fun _ => Res.bind_mono ih (fun _ _ => rfl)) h
    | fst x => exact Res.bind_mono ih (fun v _ => by cases v <;> rfl) h
    | snd x => exact Res.bind_mono ih (fun v _ => by cases v <;> rfl) h
    | binop op a b =>
      exact Res.bind_mono ih (fun va => Res.bind_mono ih (fun vb _ => by
        cases va <;> cases vb <;> rfl)) h
    | construct d c x => exact Res.bind_mono ih (fun _ _ => rfl) h
    | case x p e₁ e₂ =>
      refine Res.bind_mono ih (fun v hk => ?_) h
      rcases hm : matchPat p v with _ | vs <;> simp only [hm] at hk ⊢ <;> exact ih hk
    | fail => rfl
    | raise t message =>
      exact Res.bind_mono ih (fun v _ => by cases v <;> rfl) h

/-- **Monotonie du budget.** -/
theorem eval_fuel_mono {n m : Nat} {env : List Val} {e : Expr}
    (hle : n ≤ m) (h : eval n env e ≠ .timeout) : eval m env e = eval n env e := by
  obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le hle
  induction k with
  | zero => rfl
  | succ k ih =>
    have ih := ih (Nat.le_add_right n k)
    rw [← Nat.add_assoc, eval_succ (n + k) (by rw [ih]; exact h), ih]

end Hypomnesis.Core
