import Hypomnesis.Certificate

/-!
`hypomnesis-check` : vérifie un certificat émis par `hypomnesis check --emit-certificate`.

    lake exe hypomnesis-check check cert.json
    lake exe hypomnesis-check eval cert.json [budget]

Codes de sortie : 0 accepté, 1 rejeté par le vérificateur, 2 hors du fragment
vérifié, 3 certificat illisible, 64 usage.
-/

open Hypomnesis.Certificate Hypomnesis.Core

def exitCode : Err → UInt32
  | .illTyped _ => 1
  | .unsupported _ => 2
  | .malformed _ => 3

def load (path : String) : IO (Except Err Report) := do
  let text ← IO.FS.readFile path
  match Lean.Json.parse text with
  | .error e => return .error (.malformed s!"JSON invalide : {e}")
  | .ok json => return check json

def main (args : List String) : IO UInt32 := do
  match args with
  | ["check", path] | ["eval", path] | ["eval", path, _] =>
    match ← load path with
    | .error e =>
      IO.eprintln e.message
      return exitCode e
    | .ok r =>
      if args.head! == "check" then
        IO.println s!"accepté : programme de type {showTy r.type}"
        IO.println s!"  {r.instances} définitions vérifiées (après monomorphisation), {r.dataTypes} instances de types de données"
        unless r.skipped.isEmpty do
          IO.println s!"  non vérifiées (polymorphes, sans instance utilisée) : {", ".intercalate r.skipped}"
        return 0
      let fuel := (args.getD 2 "100000").toNat?.getD 100000
      IO.println (showRes (eval fuel [] r.program))
      return 0
  | _ =>
    IO.eprintln "usage : hypomnesis-check (check | eval) CERTIFICAT [budget]"
    return 64
