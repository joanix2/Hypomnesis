import Lean
import Hypomnesis.Effects.Handlers

open Lean Hypomnesis.Effects Hypomnesis.Effects.Handlers

def stateName : State → String
  | .created => "Created" | .validated => "Validated" | .authorized => "Authorized"
  | .dispatched => "Dispatched" | .accepted => "Accepted" | .completed => "Completed"
  | .rejected => "Rejected" | .failed => "Failed" | .timedOut => "TimedOut"
  | .unknownOutcome => "UnknownOutcome" | .dryRun => "DryRun" | .simulated => "Simulated"

def modes : List (Mode × String) :=
  [(.dryRun, "dry-run"), (.simulate, "simulate"), (.production, "production")]

def host (allowed expired valid : Bool) : Host Int Nat where
  ordinary := fun op world =>
    match op with
    | .observe _ => ⟨("sensor#1", 3), world + 1⟩
    | .act _ => ⟨⟨.failed, none⟩, world⟩
    | .solve _ => ⟨none, world + 1⟩
    | .solveTyped _ => ⟨0, world + 1⟩
    | .record _ _ _ _ => ⟨(), world + 1⟩
    | .retract _ _ => ⟨[], world + 1⟩
    | .note _ => ⟨(), world + 1⟩
  allowed := fun _ _ => allowed
  expired := fun _ _ => expired
  simulate := fun _ world =>
    ⟨if valid then ⟨.simulated, some 5⟩ else ⟨.rejected, none⟩, world + 1⟩
  production := fun _ world =>
    ⟨if valid then ⟨.completed, some 7⟩ else ⟨.failed, none⟩, world + 1⟩

def command : Handlers.Command Int := ⟨"motor", 3⟩

def program : Program Int (ActionReply Int) :=
  .request (.observe "sensor") fun input =>
  .request (.act ⟨"motor", input.2⟩) fun response =>
  if response.state = .completed then
    .request (.record "result" (response.result.getD (-1)) "reply" 0) fun _ => .done response
  else
    .request (.note "not completed") fun _ => .done response

def replyJson (response : ActionReply Int) : Json :=
  Json.mkObj [("state", Json.str (stateName response.state)), ("result", toJson response.result)]

example : (interpret .dryRun (host true false true) 3 program 0).value =
    some ⟨.dryRun, none⟩ := rfl

example : (interpret .production (host true false true) 2 program 0).dispatches = ["motor"] := rfl

example : (interpret .production (host true false true) 2 program 0).value = none := rfl

#eval IO.println (Json.mkObj [
  ("steps", toJson (modes.flatMap fun (mode, name) =>
    [false, true].flatMap fun allowed =>
      [false, true].flatMap fun expired =>
        [false, true].map fun valid =>
          let result := step mode (host allowed expired valid) (.act command) 0
          Json.mkObj [
            ("mode", Json.str name), ("allowed", Json.bool allowed),
            ("expired", Json.bool expired), ("valid", Json.bool valid),
            ("reply", replyJson result.1.value), ("world", toJson result.1.world),
            ("dispatches", toJson result.2)])),
  ("programs", toJson (modes.flatMap fun (mode, name) =>
    (List.range 5).map fun fuel =>
      let result := interpret mode (host true false true) fuel program 0
      Json.mkObj [
        ("mode", Json.str name), ("fuel", toJson fuel),
        ("value", match result.value with | none => Json.null | some r => replyJson r),
        ("world", toJson result.world), ("dispatches", toJson result.dispatches)]))
]).compress
