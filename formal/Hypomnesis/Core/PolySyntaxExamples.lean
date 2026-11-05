import Hypomnesis.Core.PolySyntax
import Hypomnesis.Core.Eval

/-! # Régressions d'effacement du Core polymorphe (HYP-023) -/

namespace Hypomnesis.Core.Poly.SyntaxExamples

open Hypomnesis.Core

def identityScheme : Scheme :=
  ⟨1, .arrow (.var 0) (.var 0)⟩

def identityAtIntAndBool : Expr :=
  .letE identityScheme (.lam (.var 0) (.var 0 []))
    (.pair
      (.app (.var 0 [.int]) (.int 7))
      (.app (.var 0 [.bool]) (.bool true)))

theorem identity_uses_two_instances_in_one_binding :
    identityAtIntAndBool.erase =
      Hypomnesis.Core.Expr.letE
        (.lam .unit (.var 0))
        (.pair
          (.app (.var 0) (.int 7))
          (.app (.var 0) (.bool true))) := rfl

theorem erased_identity_uses_the_core_evaluator :
    Hypomnesis.Core.eval 20 [] identityAtIntAndBool.erase =
      .ok (.pair (.int 7) (.bool true)) := by
  rfl

end Hypomnesis.Core.Poly.SyntaxExamples
