import Hypomnesis.Core.Check
import Hypomnesis.Core.Soundness
import Hypomnesis.Core.Eval

/-!
# Exemple : longueur d'une liste d'entiers

`int list` est l'instance 0 de la signature : `[]` porte `unit`, `::` porte
`int * int list`. Équivalent Hypomnesis :

    let rec length l = match l with [] -> 0 | _ :: t -> 1 + length t
    let n = length [1; 2; 3]
-/

namespace Hypomnesis.Core.Examples

open Hypomnesis.Core

def intList : Ty := .data 0

def sig : Sig := [[.unit, .prod .int intList]]

/-- `fix length (l : int list) : int`. Contexte du corps : `l` (0), `length` (1) ;
dans le second bras, la queue `t` est liée en 0. -/
def length : Expr :=
  .fix intList .int
    (.case (.var 0) (.ctor 0 .wild) (.int 0)
      (.case (.var 0) (.ctor 1 (.pair .wild .var))
        (.binop .add (.int 1) (.app (.var 2) (.var 0)))
        (.fail .int)))

def cons (n : Int) (tail : Expr) : Expr := .construct 0 1 (.pair (.int n) tail)

def nil : Expr := .construct 0 0 .unit

def program : Expr := .app length (cons 1 (cons 2 (cons 3 nil)))

/-- Le typage est établi par calcul, au moyen du vérificateur prouvé correct. -/
theorem program_typed : HasType sig [] program .int := by decide

/-- Donc l'exécution ne peut pas se bloquer, quel que soit le budget. -/
theorem program_never_stuck (n : Nat) : eval n [] program ≠ .stuck :=
  closed_never_stuck program_typed n

#eval eval 100 [] program

end Hypomnesis.Core.Examples
