import Lean
import Hypomnesis.Effects.Commands

open Lean Hypomnesis.Effects

def states : List (State × String) := [
  (.created, "Created"), (.validated, "Validated"), (.authorized, "Authorized"),
  (.dispatched, "Dispatched"), (.accepted, "Accepted"), (.completed, "Completed"),
  (.rejected, "Rejected"), (.failed, "Failed"), (.timedOut, "TimedOut"),
  (.unknownOutcome, "UnknownOutcome"), (.dryRun, "DryRun"), (.simulated, "Simulated")
]

theorem states_complete (s : State) : ∃ name, (s, name) ∈ states := by
  cases s <;> simp [states]

#eval IO.println (Json.mkObj [
  ("transitions", Json.arr (states.flatMap fun (source, sourceName) =>
    states.map fun (target, targetName) =>
      Json.arr #[Json.str sourceName, Json.str targetName,
        Json.bool (canMove source target)]).toArray),
  ("terminal", Json.arr (states.map fun (state, name) =>
    Json.arr #[Json.str name, Json.bool (terminal state)]).toArray),
  ("retry", Json.arr (states.flatMap fun (state, name) =>
    [false, true].flatMap fun idempotent =>
      (List.range 4).flatMap fun count =>
        (List.range 4).map fun limit =>
          Json.arr #[Json.str name, Json.bool idempotent,
            toJson (count + 1), toJson (limit + 1),
            Json.bool (mayRetry idempotent state (count + 1) (limit + 1))]).toArray)
]).compress
