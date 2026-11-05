import Hypomnesis.Core.PolyTyping
import Hypomnesis.Core.PolySyntaxExamples
import Hypomnesis.Core.Soundness
import Hypomnesis.Core.PolyTypeExamples
import Hypomnesis.Core.Fuel

/-! # Régressions du vérificateur de termes polymorphes (HYP-023) -/

namespace Hypomnesis.Core.Poly.TypingExamples

open Hypomnesis.Core

example : LawfulBEq Ty := by infer_instance

theorem identity_polymorphic_let_checks_at_two_types :
    (typeOf [] 0 [] SyntaxExamples.identityAtIntAndBool).map
      (· == .prod .int .bool) = some true := by native_decide

theorem identity_polymorphic_let_has_declarative_type :
    HasType [] 0 [] SyntaxExamples.identityAtIntAndBool (.prod .int .bool) := by
  apply HasType.letE
  · simp [SyntaxExamples.identityScheme, Scheme.wellScoped, Ty.wellScoped]
  · apply HasType.lam
    · simp [SyntaxExamples.identityScheme, Ty.wellScoped]
    · exact .var (by rfl) (by simp [mono, Scheme.instantiate, instantiateSubst,
        Ty.subst]) (by simp)
  · apply HasType.pair
    · apply HasType.app
      · show HasType [] 0 [SyntaxExamples.identityScheme]
          (.var 0 [.int]) (.arrow .int .int)
        exact .var (by rfl) (by simp [SyntaxExamples.identityScheme, Scheme.instantiate,
          instantiateSubst, Ty.subst]) (by simp [Ty.wellScoped])
      · exact .int
    · apply HasType.app
      · show HasType [] 0 [SyntaxExamples.identityScheme]
          (.var 0 [.bool]) (.arrow .bool .bool)
        exact .var (by rfl) (by simp [SyntaxExamples.identityScheme, Scheme.instantiate,
          instantiateSubst, Ty.subst]) (by simp [Ty.wellScoped])
      · exact .bool

theorem identity_polymorphic_let_checker_is_complete :
    typeOf [] 0 [] SyntaxExamples.identityAtIntAndBool = some (.prod .int .bool) :=
  typeOf_complete (by rfl) (by rfl) identity_polymorphic_let_has_declarative_type

theorem identity_polymorphic_let_is_checked_and_evaluated :
    typeOf [] 0 [] SyntaxExamples.identityAtIntAndBool = some (.prod .int .bool) ∧
    eval 20 [] SyntaxExamples.identityAtIntAndBool.erase =
      .ok (.pair (.int 7) (.bool true)) := by
  exact ⟨identity_polymorphic_let_checker_is_complete,
    SyntaxExamples.erased_identity_uses_the_core_evaluator⟩

theorem identity_polymorphic_let_is_safe_at_fuel_20 :
    Core.Safe [] (eval 20 [] SyntaxExamples.identityAtIntAndBool.erase)
      (.prod .int .bool) := by
  rw [SyntaxExamples.erased_identity_uses_the_core_evaluator]
  change Core.ValTy [] (.pair (.int 7) (.bool true)) (.prod .int .bool)
  exact .pair .int .bool

theorem identity_polymorphic_let_is_safe_at_any_fuel (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] SyntaxExamples.identityAtIntAndBool.erase)
      (.prod .int .bool) := by
  have evalAtTwenty :
      Core.eval 20 [] SyntaxExamples.identityAtIntAndBool.erase =
        .ok (.pair (.int 7) (.bool true)) :=
    SyntaxExamples.erased_identity_uses_the_core_evaluator
  by_cases fuelLeTwenty : fuel ≤ 20
  · by_cases timedOut : Core.eval fuel [] SyntaxExamples.identityAtIntAndBool.erase = .timeout
    · simp [Core.Safe, timedOut]
    · have stable := Core.eval_fuel_mono fuelLeTwenty timedOut
      rw [← stable, evalAtTwenty]
      exact .pair .int .bool
  · have twentyLeFuel : 20 ≤ fuel := Nat.le_of_not_ge fuelLeTwenty
    have evalAtTwentyNotTimeout :
        Core.eval 20 [] SyntaxExamples.identityAtIntAndBool.erase ≠ .timeout := by
      rw [evalAtTwenty]
      simp
    have stable :=
      Core.eval_fuel_mono twentyLeFuel evalAtTwentyNotTimeout
    rw [stable, evalAtTwenty]
    exact .pair .int .bool

open Examples in
def genericMapValue : Expr :=
  .fix (.arrow (.var 0) (.var 1))
    (.arrow (list (.var 0)) (list (.var 1)))
    (.lam (list (.var 0))
      (.case (.var 0 []) (.ctor 0 .wild)
        (.construct 0 0 [.var 1] .unit)
        (.case (.var 0 []) (.ctor 1 (.pair .var .var))
          (.construct 0 1 [.var 1]
            (.pair (.app (.var 3 []) (.var 1 []))
              (.app (.app (.var 4 []) (.var 3 [])) (.var 0 []))))
          (.fail (list (.var 1))))))

open Examples in
def intList : Expr :=
  .construct 0 1 [.int]
    (.pair (.int 2)
      (.construct 0 1 [.int]
        (.pair (.int 3) (.construct 0 0 [.int] .unit))))

open Examples in
def boolList : Expr :=
  .construct 0 1 [.bool]
    (.pair (.bool true)
      (.construct 0 1 [.bool]
        (.pair (.bool false) (.construct 0 0 [.bool] .unit))))

open Examples in
def mapTwoInstances : Expr :=
  .letE (Scheme.mk 2
      (.arrow (.arrow (.var 0) (.var 1))
        (.arrow (list (.var 0)) (list (.var 1)))))
    genericMapValue
    (.pair
      (.app (.app (.var 0 [.int, .bool]) (.lam .int (.bool true))) intList)
      (.app (.app (.var 0 [.bool, .int]) (.lam .bool (.int 1))) boolList))

theorem generic_map_checks_with_two_instances :
    (typeOf Examples.listSig 0 [] mapTwoInstances).map
      (· == .prod (Examples.list .bool) (Examples.list .int)) = some true := by
  native_decide

theorem generic_map_has_type :
    typeOf Examples.listSig 0 [] mapTwoInstances =
      some (.prod (Examples.list .bool) (Examples.list .int)) := by
  have checked := generic_map_checks_with_two_instances
  cases hType : typeOf Examples.listSig 0 [] mapTwoInstances with
  | none => simp [hType] at checked
  | some inferred =>
    have hbeq : (inferred == .prod (Examples.list .bool) (Examples.list .int)) = true := by
      simpa [hType] using checked
    have hEq := Ty.beq_eq_true hbeq
    rw [hEq]

theorem generic_map_runs_with_two_instances :
    Core.eval 300 [] mapTwoInstances.erase =
      .ok (.pair
        (.con 1 (.pair (.bool true)
          (.con 1 (.pair (.bool true) (.con 0 .unit)))))
        (.con 1 (.pair (.int 1)
          (.con 1 (.pair (.int 1) (.con 0 .unit)))))) := by
  rfl

def identityWithWrongArity : Expr :=
  .letE SyntaxExamples.identityScheme
    (.lam (.var 0) (.var 0 []))
    (.app (.var 0 [.int, .bool]) (.int 7))

theorem local_instantiation_with_wrong_arity_rejected :
    (typeOf [] 0 [] identityWithWrongArity).isNone = true := by native_decide

def identityWithWrongValue : Expr :=
  .letE SyntaxExamples.identityScheme (.int 7) (.int 0)

theorem generalized_value_must_match_scheme :
    (typeOf [] 0 [] identityWithWrongValue).isNone = true := by native_decide

def openPair : Expr :=
  .pair (.var 0 []) (.var 1 [])

def openPairEnvironment : TyEnv :=
  [mono (.var 0), mono (.var 1)]

def specializePairType : Nat → Ty
  | 0 => .int
  | 1 => .bool
  | index + 2 => .var index

theorem open_pair_checks_at_open_types :
    (typeOf [] 2 openPairEnvironment openPair).map
      (· == .prod (.var 0) (.var 1)) = some true := by
  native_decide

theorem open_pair_has_declarative_type :
    HasType [] 2 openPairEnvironment openPair (.prod (.var 0) (.var 1)) := by
  apply HasType.pair
  · exact .var (by rfl) (by simp) (by rfl)
  · exact .var (by rfl) (by simp) (by rfl)

theorem type_substitution_preserves_open_pair :
    HasType [] 0 [mono .int, mono .bool] openPair (.prod .int .bool) := by
  have htyped := open_pair_has_declarative_type
  have hpreserved := HasType.subst (sig := []) (depth := 2)
    (env := openPairEnvironment) (expr := openPair)
    (type := .prod (.var 0) (.var 1)) rfl htyped specializePairType 0 (by
      intro index hindex
      cases index with
      | zero => simp [specializePairType, Ty.wellScoped]
      | succ index =>
        cases index with
        | zero => simp [specializePairType, Ty.wellScoped]
        | succ index => omega)
  simpa [openPairEnvironment, openPair, specializePairType, mono, TyEnv.subst,
    Scheme.subst, lift, Ty.subst, Ty.rename, Ty.rename_id, Expr.subst] using hpreserved

end Hypomnesis.Core.Poly.TypingExamples
