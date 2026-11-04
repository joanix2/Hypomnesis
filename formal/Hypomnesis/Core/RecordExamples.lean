import Hypomnesis.Core.Records

/-! # `deposit` : le solde augmente, le propriétaire reste identique.
Les caractères du propriétaire sont encodés en liste de points de code :
cet exemple de records ne prétend pas ajouter les primitives string de HYP-150.
-/

namespace Hypomnesis.Core.Records.Examples

def fields : List Ty := [.data 1, .int]
def sig : Sig := [[payloadTy fields], [.unit, .prod .int (.data 1)]]

def owner : Expr :=
  [97, 108, 105, 99, 101].foldr
    (fun c rest => .construct 1 1 (.pair (.int c) rest)) (.construct 1 0 .unit)

def alice : Expr := make 0 [owner, .int 100]

def deposit : Expr :=
  .lam .int (.lam (.data 0)
    (.app (.app (update 0 1 fields .int)
      (.binop .add (.app (get 0 1 .int) (.var 0)) (.var 1))) (.var 0)))

def program : Expr := .app (.app deposit (.int 50)) alice

theorem program_typed : HasType sig [] program (.data 0) := by decide

theorem program_never_stuck (fuel : Nat) : eval fuel [] program ≠ .stuck :=
  closed_never_stuck program_typed fuel

theorem deposit_balance : eval 100 [] (.app (get 0 1 .int) program) = .ok (.int 150) := by
  rfl

theorem deposit_owner : eval 100 [] (.app (get 0 0 (.data 1)) program) = eval 100 [] owner := by
  rfl

#eval eval 100 [] (.app (get 0 1 .int) program)

end Hypomnesis.Core.Records.Examples
