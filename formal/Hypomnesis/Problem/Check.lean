import Init.Data.Rat
import Std

/-!
# Faisabilité indépendante du solveur (HYP-053)

Projection des domaines et contraintes d'une Problem IR normalisée.
Les réels sont des rationnels exacts ; booléens et nombres restent distincts.
Ni l'objectif ni les données de planification ne participent au contrôle.
-/

namespace Hypomnesis.Problem

inductive Kind where
  | real | integer | boolean
  deriving DecidableEq, Repr

inductive Scalar where
  | number (value : Rat)
  | boolean (value : Bool)
  | invalid
  deriving DecidableEq, Repr

abbrev Assignment := List (String × Scalar)

structure Variable where
  name : String
  kind : Kind
  lower : Option Rat
  upper : Option Rat
  choices : List Scalar

inductive Relation where
  | le | ge | eq
  deriving DecidableEq, Repr

structure Constraint where
  terms : List (String × Rat)
  relation : Relation
  rhs : Rat

structure Problem where
  variables : List Variable
  constraints : List Constraint

def InDomain (v : Variable) : Scalar → Prop
  | .invalid => False
  | .boolean b =>
    v.kind = .boolean ∧
      (v.choices = [] ∨ Scalar.boolean b ∈ v.choices)
  | .number q =>
    v.kind ≠ .boolean ∧
      (v.kind = .integer → q.den = 1) ∧
      (match v.lower with | none => True | some lo => lo ≤ q) ∧
      (match v.upper with | none => True | some hi => q ≤ hi) ∧
      (v.choices = [] ∨ Scalar.number q ∈ v.choices)

instance (v : Variable) (value : Scalar) : Decidable (InDomain v value) := by
  cases value with
  | invalid => exact isFalse id
  | boolean b => unfold InDomain; infer_instance
  | number q =>
    unfold InDomain
    cases v.lower <;> cases v.upper <;> infer_instance

/-- Boolean values have numeric meaning only in linear constraints. -/
def numeric : Scalar → Option Rat
  | .number q => some q
  | .boolean b => some (if b then 1 else 0)
  | .invalid => none

def evalLinear (assignment : Assignment) : List (String × Rat) → Option Rat
  | [] => some 0
  | (name, coefficient) :: rest => do
    let value ← assignment.lookup name
    let q ← numeric value
    let tail ← evalLinear assignment rest
    pure (coefficient * q + tail)

/-- Relational meaning, independent of the executable Option fold. -/
inductive LinearValue (assignment : Assignment) : List (String × Rat) → Rat → Prop where
  | nil : LinearValue assignment [] 0
  | cons (found : assignment.lookup name = some value) (number : numeric value = some q)
      (tail : LinearValue assignment rest total) :
      LinearValue assignment ((name, coefficient) :: rest) (coefficient * q + total)

theorem evalLinear_sound (assignment : Assignment) (terms : List (String × Rat)) (q : Rat)
    (accepted : evalLinear assignment terms = some q) :
    LinearValue assignment terms q := by
  induction terms generalizing q with
  | nil =>
    simp [evalLinear] at accepted
    subst q
    exact .nil
  | cons term rest ih =>
    rcases term with ⟨name, coefficient⟩
    cases found : assignment.lookup name with
    | none => simp [evalLinear, found] at accepted
    | some value =>
      cases number : numeric value with
      | none => simp [evalLinear, found, number] at accepted
      | some head =>
        cases tail : evalLinear assignment rest with
        | none => simp [evalLinear, found, tail] at accepted
        | some total =>
          simp [evalLinear, found, number, tail] at accepted
          subst q
          exact .cons found number (ih total tail)

theorem evalLinear_complete (assignment : Assignment) (terms : List (String × Rat)) (q : Rat)
    (meaning : LinearValue assignment terms q) :
    evalLinear assignment terms = some q := by
  induction meaning with
  | nil => rfl
  | cons found number _ ih => simp [evalLinear, found, number, ih]

def Holds : Relation → Rat → Rat → Prop
  | .le, lhs, rhs => lhs ≤ rhs
  | .ge, lhs, rhs => rhs ≤ lhs
  | .eq, lhs, rhs => lhs = rhs

instance (relation : Relation) (lhs rhs : Rat) : Decidable (Holds relation lhs rhs) := by
  cases relation <;> unfold Holds <;> infer_instance

def checkVariable (assignment : Assignment) (v : Variable) : Bool :=
  match assignment.lookup v.name with
  | none => false
  | some value => decide (InDomain v value)

def checkConstraint (assignment : Assignment) (constraint : Constraint) : Bool :=
  match evalLinear assignment constraint.terms with
  | none => false
  | some lhs => decide (Holds constraint.relation lhs constraint.rhs)

def check (problem : Problem) (assignment : Assignment) : Bool :=
  assignment.all (fun pair => problem.variables.any (fun v => v.name == pair.1)) &&
    problem.variables.all (checkVariable assignment) &&
    problem.constraints.all (checkConstraint assignment)

structure Satisfies (problem : Problem) (assignment : Assignment) : Prop where
  known : ∀ pair ∈ assignment, ∃ v ∈ problem.variables, v.name = pair.1
  domains : ∀ v ∈ problem.variables,
    ∃ value, assignment.lookup v.name = some value ∧ InDomain v value
  constraints : ∀ constraint ∈ problem.constraints, ∃ lhs,
    LinearValue assignment constraint.terms lhs ∧ Holds constraint.relation lhs constraint.rhs

theorem check_sound (problem : Problem) (assignment : Assignment)
    (accepted : check problem assignment = true) : Satisfies problem assignment := by
  simp only [check, Bool.and_eq_true] at accepted
  rcases accepted with ⟨⟨known, domains⟩, constraints⟩
  constructor
  · intro pair member
    have key := List.all_eq_true.mp known pair member
    simpa using List.any_eq_true.mp key
  · intro v member
    have domain := List.all_eq_true.mp domains v member
    cases found : assignment.lookup v.name with
    | none => simp [checkVariable, found] at domain
    | some value =>
      exact ⟨value, rfl, of_decide_eq_true (by simpa [checkVariable, found] using domain)⟩
  · intro constraint member
    have holds := List.all_eq_true.mp constraints constraint member
    cases evaluated : evalLinear assignment constraint.terms with
    | none => simp [checkConstraint, evaluated] at holds
    | some lhs =>
      exact ⟨lhs, evalLinear_sound assignment constraint.terms lhs evaluated,
        of_decide_eq_true (by simpa [checkConstraint, evaluated] using holds)⟩

theorem check_complete (problem : Problem) (assignment : Assignment)
    (meaning : Satisfies problem assignment) : check problem assignment = true := by
  simp only [check, Bool.and_eq_true]
  refine ⟨⟨List.all_eq_true.mpr ?_, List.all_eq_true.mpr ?_⟩, List.all_eq_true.mpr ?_⟩
  · intro pair member
    rcases meaning.known pair member with ⟨v, member, same⟩
    exact List.any_eq_true.mpr ⟨v, member, by simpa using same⟩
  · intro v member
    rcases meaning.domains v member with ⟨value, found, domain⟩
    simp [checkVariable, found, domain]
  · intro constraint member
    rcases meaning.constraints constraint member with ⟨lhs, value, holds⟩
    simp [checkConstraint, evalLinear_complete assignment constraint.terms lhs value, holds]

end Hypomnesis.Problem
