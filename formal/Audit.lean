/-
  Audit des axiomes des théorèmes principaux.
  La CI échoue si la sortie mentionne `sorryAx` ou un axiome autre que
  `propext`, `Quot.sound` et `Classical.choice`.
  Usage : lake env lean Audit.lean
-/
import Hypomnesis

open Hypomnesis.Core Hypomnesis.Epistemics

#print axioms eval_safe
#print axioms closed_never_stuck
#print axioms typeOf_sound
#print axioms typeOf_complete
#print axioms hasType_unique
#print axioms eval_fuel_mono
#print axioms matchPat_sound
#print axioms patTypeOf_sound
#print axioms patTypeOf_complete
#print axioms Examples.program_typed
#print axioms Examples.program_never_stuck
#print axioms Prov.eval_subst
#print axioms holds_after_retract
#print axioms retract_unrelated
#print axioms support_mono
#print axioms conjunction_no_stronger
#print axioms Hypomnesis.Effects.dispatch_ordered
#print axioms Hypomnesis.Effects.dispatch_permitted
#print axioms Hypomnesis.Effects.no_dispatch_without_permission
#print axioms Hypomnesis.Effects.Execution.toRun
#print axioms Hypomnesis.Effects.non_idempotent_at_most_once
#print axioms Hypomnesis.Effects.attempts_bounded
#print axioms Hypomnesis.Effects.terminal_absorbing
