namespace Hypomnesis.Effects

inductive State where
  | created | validated | authorized | dispatched | accepted | completed
  | rejected | failed | timedOut | unknownOutcome | dryRun | simulated
  deriving DecidableEq, Repr

open State

def canMove : State → State → Bool
  | created, validated | created, rejected => true
  | validated, authorized | validated, rejected => true
  | authorized, dispatched | authorized, dryRun | authorized, simulated
  | authorized, rejected | authorized, timedOut => true
  | dispatched, dispatched | dispatched, accepted | dispatched, completed
  | dispatched, failed | dispatched, timedOut | dispatched, unknownOutcome => true
  | accepted, completed | accepted, failed | accepted, timedOut
  | accepted, unknownOutcome => true
  | _, _ => false

/-- A single command's journal, newest event first, under its fixed host permission. -/
inductive Run (permitted : Prop) : State → List State → Prop
  | init : Run permitted created [created]
  | advance {s t history} :
      Run permitted s history →
      canMove s t = true →
      (t = authorized → permitted) →
      Run permitted t (t :: history)

theorem into_authorized {s} (edge : canMove s authorized = true) : s = validated := by
  cases s <;> simp_all [canMove]

theorem into_dispatched {s} (edge : canMove s dispatched = true) :
    s = authorized ∨ s = dispatched := by
  cases s <;> simp_all [canMove]

theorem run_head {p s history} (run : Run p s history) :
    ∃ tail, history = s :: tail := by
  cases run with
  | init => exact ⟨[], rfl⟩
  | advance _ _ _ => exact ⟨_, rfl⟩

theorem authorized_shape {p s history} (run : Run p s history) (state : s = authorized) :
    ∃ tail, history = authorized :: validated :: tail := by
  subst s
  cases run with
  | advance prior edge grant =>
      have previous := into_authorized edge
      obtain ⟨tail, shape⟩ := run_head prior
      exact ⟨tail, by simp [shape, previous]⟩

theorem dispatched_shape {p s history} (run : Run p s history) (state : s = dispatched) :
    ∃ gap tail, history = dispatched :: (gap ++ authorized :: validated :: tail) := by
  induction run with
  | init => cases state
  | @advance before after history prior edge grant ih =>
      subst after
      rcases into_dispatched edge with previous | previous
      · obtain ⟨tail, shape⟩ := authorized_shape prior previous
        exact ⟨[], tail, by simp [shape]⟩
      · obtain ⟨gap, tail, shape⟩ := ih previous
        exact ⟨dispatched :: gap, tail, by simp [shape]⟩

/-- Each dispatch occurrence has older authorization, itself immediately after validation. -/
def DispatchOrdered (history : List State) : Prop :=
  ∀ newer older, history = newer ++ dispatched :: older →
    ∃ gap tail, older = gap ++ authorized :: validated :: tail

theorem dispatch_ordered {p s history} (run : Run p s history) : DispatchOrdered history := by
  induction run with
  | init =>
      intro newer older equality
      have member : dispatched ∈ [created] := by rw [equality]; simp
      simp at member
  | @advance before after history prior edge grant ih =>
      intro newer older equality
      cases newer with
      | nil =>
          simp only [List.nil_append, List.cons.injEq] at equality
          obtain ⟨rfl, rfl⟩ := equality
          obtain ⟨gap, tail, shape⟩ := dispatched_shape (Run.advance prior edge grant) rfl
          exact ⟨gap, tail, (List.cons.inj shape).2⟩
      | cons head rest =>
          simp only [List.cons_append, List.cons.injEq] at equality
          exact ih rest older equality.2

theorem authorized_permitted {p s history} (run : Run p s history)
    (member : authorized ∈ history) : p := by
  induction run with
  | init => simp at member
  | advance prior edge grant ih =>
      rcases List.mem_cons.mp member with current | older
      · exact grant current.symm
      · exact ih older

theorem dispatch_permitted {p s history} (run : Run p s history)
    (member : dispatched ∈ history) : p := by
  obtain ⟨newer, older, equality⟩ := List.mem_iff_append.mp member
  obtain ⟨gap, tail, shape⟩ := dispatch_ordered run newer older equality
  apply authorized_permitted run
  rw [equality, shape]
  simp

theorem no_dispatch_without_permission {p s history} (run : Run p s history)
    (denied : ¬ p) : dispatched ∉ history :=
  fun member => denied (dispatch_permitted run member)

end Hypomnesis.Effects
