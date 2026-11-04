import Lean
import Hypomnesis.Effects.Dispatch

open Lean Hypomnesis.Effects

def states : List (State × String) := [
  (.created, "Created"), (.validated, "Validated"), (.authorized, "Authorized"),
  (.dispatched, "Dispatched"), (.accepted, "Accepted"), (.completed, "Completed"),
  (.rejected, "Rejected"), (.failed, "Failed"), (.timedOut, "TimedOut"),
  (.unknownOutcome, "UnknownOutcome"), (.dryRun, "DryRun"), (.simulated, "Simulated")
]

theorem states_complete (s : State) : ∃ name, (s, name) ∈ states := by
  cases s <;> simp [states]

#eval IO.println (Json.arr (states.flatMap fun (source, sourceName) =>
  states.map fun (target, targetName) =>
    Json.arr #[Json.str sourceName, Json.str targetName,
      Json.bool (canMove source target)]).toArray).compress
