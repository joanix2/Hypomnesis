import Hypomnesis.Core.Covered

/-! # Exemple récursif dont tous les filtrages sont certifiés -/

namespace Hypomnesis.Core.Coverage.Examples

def listTy : Ty := .data 0
def sig : Sig := [[.unit, .prod .int listTy]]

def arms : List (Pat × Expr) := [
  (.ctor 0 .wild, .int 0),
  (.ctor 1 (.pair .wild .var), .binop .add (.int 1) (.app (.var 3) (.var 0)))]

def boundTypes : (Pat × Expr) → Ctx
  | (.ctor 1 _, _) => [listTy]
  | _ => []

def length : Expr :=
  .fix listTy .int (.letE (.var 0) (caseChain 0 .int arms))

theorem length_certified : Certified sig [] length (.arrow listTy .int) := by
  apply Certified.fix
  apply Certified.matchE (fuel := 10) boundTypes (Certified.var rfl) (by decide)
  · intro arm member
    simp only [arms, List.mem_cons, List.not_mem_nil, or_false] at member
    rcases member with rfl | rfl
    · exact .ctor rfl rfl .wild
    · exact .ctor rfl rfl (.pair .wild .var)
  · intro arm member
    simp only [arms, List.mem_cons, List.not_mem_nil, or_false] at member
    rcases member with rfl | rfl
    · exact .int
    · exact .binop .int (.app (.var rfl) (.var rfl))

def nil : Expr := .construct 0 0 .unit
def cons (n : Int) (tail : Expr) : Expr := .construct 0 1 (.pair (.int n) tail)

theorem cons_certified {n : Int} {tail : Expr} (h : Certified sig [] tail listTy) :
    Certified sig [] (cons n tail) listTy :=
  .construct rfl rfl (.pair .int h)

def program : Expr := .app length (cons 1 (cons 2 (cons 3 nil)))

theorem program_certified : Certified sig [] program .int :=
  .app length_certified (cons_certified (cons_certified (cons_certified
    (.construct rfl rfl .unit))))

theorem program_typed : HasType sig [] program .int := program_certified.typed

theorem program_no_matchFail (fuel : Nat) : eval fuel [] program ≠ .matchFail :=
  certified_program_no_matchFail program_certified fuel

theorem length_three : eval 100 [] program = .ok (.int 3) := by rfl

example : exhaustive [] 0 .bool [.wild] = none := rfl
example : exhaustive [] 10 .bool [.bool true, .bool false] = some true := rfl
example : exhaustive [] 10 .bool [.bool true] = some false := rfl

def guardedArms : List Arm := [
  ⟨.wild, true, .int 99⟩,
  ⟨.bool true, false, .int 1⟩,
  ⟨.bool false, false, .int 0⟩]

theorem guards_cannot_remove_the_cover (guard : Arm → List Val → Bool)
    (b : Bool) :
    ∃ chosen bindings, select guard (.bool b) guardedArms = some (chosen, bindings) :=
  guarded_exhaustive_selects (by decide : exhaustive [] 10 .bool
    (unguarded guardedArms) = some true) .bool guard

def booleanArms : List (Pat × Expr) := [(.bool true, .int 1), (.bool false, .int 0)]

theorem boolean_arms_certified :
    Certified [] [.bool] (caseChain 0 .int booleanArms) .int := by
  apply Certified.casesE (fuel := 10) (tx := .bool) (fun _ => []) rfl (by decide)
  · intro arm member
    simp only [booleanArms, List.mem_cons, List.not_mem_nil, or_false] at member
    rcases member with rfl | rfl <;> exact .bool
  · intro arm member
    simp only [booleanArms, List.mem_cons, List.not_mem_nil, or_false] at member
    rcases member with rfl | rfl <;> exact .int

/-- Le code Core réel d'un premier bras `_ when false`, suivi de true/false.
La garde duplique la suite sans réessayer un bras déjà sélectionné. -/
def guardedProgram : Expr :=
  .letE (.bool true)
    (.case (.var 0) .wild
      (.ite (.bool false) (.int 99) (caseChain 0 .int booleanArms))
      (caseChain 0 .int booleanArms))

theorem guarded_program_certified : Certified [] [] guardedProgram .int :=
  .letE .bool (.case (.var rfl) .wild
    (.ite .bool .int boolean_arms_certified) boolean_arms_certified)

theorem guarded_program_no_matchFail (fuel : Nat) :
    eval fuel [] guardedProgram ≠ .matchFail :=
  certified_program_no_matchFail guarded_program_certified fuel

theorem false_guard_uses_the_next_arm : eval 20 [] guardedProgram = .ok (.int 1) := rfl

end Hypomnesis.Core.Coverage.Examples
