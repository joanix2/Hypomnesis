import Hypomnesis.Effects.Dispatch

namespace Hypomnesis.Effects

open State

def attempts : List State → Nat
  | [] => 0
  | state :: history => attempts history + if state = dispatched then 1 else 0

def mayRetry (idempotent : Bool) (state : State) (count limit : Nat) : Bool :=
  idempotent && decide (state = dispatched) && decide (count < limit)

def terminal : State → Bool
  | completed | rejected | failed | timedOut | unknownOutcome | dryRun | simulated => true
  | _ => false

inductive Event where
  | moved (state : State)
  | lostResponse
  | duplicateRequest
  deriving DecidableEq, Repr

/-- Local dispatcher execution; duplicates retain the cached command journal. -/
inductive Execution (idempotent : Bool) (limit : Nat) (permitted : Prop) :
    State → List State → List Event → Prop
  | init : Execution idempotent limit permitted created [created] [.moved created]
  | advance {s t history events} :
      Execution idempotent limit permitted s history events →
      canMove s t = true →
      (t = authorized → permitted) →
      (s = dispatched ∧ t = dispatched →
        mayRetry idempotent s (attempts history) limit = true) →
      Execution idempotent limit permitted t (t :: history) (.moved t :: events)
  | lost {history events} :
      Execution idempotent limit permitted dispatched history events →
      Execution idempotent limit permitted dispatched history (.lostResponse :: events)
  | duplicate {s history events} :
      Execution idempotent limit permitted s history events →
      Execution idempotent limit permitted s history (.duplicateRequest :: events)

theorem Execution.toRun {i limit p s history events}
    (run : Execution i limit p s history events) : Run p s history := by
  induction run with
  | init => exact .init
  | advance _ edge grant _ ih => exact .advance ih edge grant
  | lost _ ih => exact ih
  | duplicate _ ih => exact ih

theorem early_predecessor {s t} (edge : canMove s t = true)
    (early : t = created ∨ t = validated ∨ t = authorized) :
    s = created ∨ s = validated ∨ s = authorized := by
  cases s <;> cases t <;> simp_all [canMove]

theorem attempts_zero_early {i limit p s history events}
    (run : Execution i limit p s history events)
    (early : s = created ∨ s = validated ∨ s = authorized) :
    attempts history = 0 := by
  induction run with
  | init => rfl
  | @advance before after history events prior edge grant retry ih =>
      have zero := ih (early_predecessor edge early)
      have notDispatch : after ≠ dispatched := by
        rcases early with h | h | h <;> simp [h]
      simp [attempts, zero, notDispatch]
  | lost _ _ => simp at early
  | duplicate _ ih => exact ih early

theorem non_idempotent_at_most_once {limit p s history events}
    (run : Execution false limit p s history events) : attempts history ≤ 1 := by
  induction run with
  | init => decide
  | @advance before after history events prior edge grant retry ih =>
      by_cases dispatch : after = dispatched
      · rcases into_dispatched (dispatch ▸ edge) with previous | previous
        · have zero := attempts_zero_early prior (Or.inr (Or.inr previous))
          simp [attempts, zero, dispatch]
        · have allowed := retry ⟨previous, dispatch⟩
          simp [mayRetry] at allowed
      · simpa [attempts, dispatch] using ih
  | lost _ ih => exact ih
  | duplicate _ ih => exact ih

theorem attempts_bounded {i limit p s history events}
    (run : Execution i limit p s history events) (positive : 0 < limit) :
    attempts history ≤ limit := by
  induction run with
  | init => simp [attempts]
  | @advance before after history events prior edge grant retry ih =>
      by_cases dispatch : after = dispatched
      · rcases into_dispatched (dispatch ▸ edge) with previous | previous
        · have zero := attempts_zero_early prior (Or.inr (Or.inr previous))
          simp [attempts, zero, dispatch]
          omega
        · have allowed := retry ⟨previous, dispatch⟩
          have room : attempts history < limit := by
            simp [mayRetry, previous] at allowed
            exact allowed.2
          simp only [attempts, ite_eq_left dispatch]
          omega
      · simpa [attempts, dispatch] using ih
  | lost _ ih => exact ih
  | duplicate _ ih => exact ih

theorem terminal_absorbing {s t} (ended : terminal s = true) : canMove s t = false := by
  cases s <;> cases t <;> simp_all [terminal, canMove]

example : Execution false 5 True unknownOutcome
    [unknownOutcome, dispatched, authorized, validated, created]
    [.moved unknownOutcome, .duplicateRequest, .lostResponse, .moved dispatched,
      .moved authorized, .moved validated, .moved created] := by
  have v : Execution false 5 True validated [validated, created]
      [.moved validated, .moved created] :=
    .advance .init (by decide) (fun _ => True.intro) (by simp)
  have a : Execution false 5 True authorized [authorized, validated, created]
      [.moved authorized, .moved validated, .moved created] :=
    .advance v (by decide) (fun _ => True.intro) (by simp)
  have d : Execution false 5 True dispatched [dispatched, authorized, validated, created]
      [.moved dispatched, .moved authorized, .moved validated, .moved created] :=
    .advance a (by decide) (fun _ => True.intro) (by simp)
  exact .advance (.duplicate (.lost d)) (by decide) (fun _ => True.intro) (by simp)

end Hypomnesis.Effects
