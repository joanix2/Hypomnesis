/-
  Audit des axiomes des théorèmes principaux.
  La CI échoue si la sortie mentionne `sorryAx` ou un axiome autre que
  `propext`, `Quot.sound` et `Classical.choice`.
  Usage : lake env lean Audit.lean
-/
import Hypomnesis

open Hypomnesis.Core Hypomnesis.Epistemics

#print axioms eval_safe
#print axioms evalOp_ty
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
#print axioms Records.payload_typed
#print axioms Records.project_typed
#print axioms Records.replaceAt_typed
#print axioms Records.make_typed
#print axioms Records.get_typed
#print axioms Records.update_typed
#print axioms Records.update_checked
#print axioms Records.update_never_stuck
#print axioms Records.get_never_stuck
#print axioms Records.Examples.program_typed
#print axioms Records.Examples.program_never_stuck
#print axioms Records.Examples.deposit_balance
#print axioms Records.Examples.deposit_owner
#print axioms Prov.eval_subst
#print axioms holds_after_retract
#print axioms retract_unrelated
#print axioms support_mono
#print axioms conjunction_no_stronger
#print axioms Revision.candidate_complete
#print axioms Revision.invalidated_eq_full
#print axioms Revision.revise_incr_eq_full
#print axioms Revision.journal_prefix
#print axioms Hypomnesis.Epistemics.Conflicts.no_false_conflict
#print axioms Hypomnesis.Contracts.decode_encode
#print axioms Hypomnesis.Contracts.encode_conforms
#print axioms Hypomnesis.Effects.dispatch_ordered
#print axioms Hypomnesis.Effects.dispatch_permitted
#print axioms Hypomnesis.Effects.no_dispatch_without_permission
#print axioms Hypomnesis.Effects.Execution.toRun
#print axioms Hypomnesis.Effects.non_idempotent_at_most_once
#print axioms Hypomnesis.Effects.attempts_bounded
#print axioms Hypomnesis.Effects.terminal_absorbing
#print axioms Hypomnesis.Effects.Handlers.dry_run_no_dispatch
#print axioms Hypomnesis.Effects.Handlers.simulation_no_dispatch
#print axioms Hypomnesis.Effects.Handlers.dry_action_unchanged
#print axioms Hypomnesis.Effects.Handlers.ordinary_answers_shared
#print axioms Hypomnesis.Effects.Handlers.handlers_interpret_same_term
#print axioms Hypomnesis.Effects.Handlers.equal_answers_equal_results
#print axioms Hypomnesis.Problem.evalLinear_sound
#print axioms Hypomnesis.Problem.evalLinear_complete
#print axioms Hypomnesis.Problem.check_sound
#print axioms Hypomnesis.Problem.check_complete
