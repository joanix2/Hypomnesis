import Hypomnesis.Effects.Dispatch

/-!
# Un terme d'effets, trois handlers (HYP-067)

Les continuations reçoivent les réponses réellement sélectionnées et l'état
hôte évolue explicitement. Les traces recensent les handoffs au callback de
production, pas ses retries/acquittements (HYP-066). Le budget compte les
opérations ; la terminaison des callbacks hôtes n'est pas prouvée.
-/

namespace Hypomnesis.Effects.Handlers

inductive Mode where
  | dryRun | simulate | production
  deriving DecidableEq, Repr

structure Command (Data : Type) where
  actuator : String
  payload : Data

structure ActionReply (Data : Type) where
  state : State
  result : Option Data

inductive Operation (Data : Type) : Type → Type where
  | observe (sensor : String) : Operation Data (String × Data)
  | act (command : Command Data) : Operation Data (ActionReply Data)
  | solve (problem : Data) : Operation Data (Option Data)
  | solveTyped (problem : Data) : Operation Data Data
  | record (key : String) (value : Data) (method : String) (support : Data) :
      Operation Data Unit
  | retract (key reason : String) : Operation Data (List String)
  | note (text : String) : Operation Data Unit

inductive Program (Data Result : Type) : Type 1 where
  | done (value : Result)
  | request {Reply : Type} (op : Operation Data Reply) (next : Reply → Program Data Result)

structure Reply (World Result : Type) where
  value : Result
  world : World

structure Host (Data World : Type) where
  ordinary : {Result : Type} → Operation Data Result → World → Reply World Result
  allowed : Command Data → World → Bool
  expired : Command Data → World → Bool
  simulate : Command Data → World → Reply World (ActionReply Data)
  production : Command Data → World → Reply World (ActionReply Data)

/-- Mode selection after the common contract/permission/business/safety gates. -/
def step (mode : Mode) (host : Host Data World) (op : Operation Data Result)
    (world : World) : Reply World Result × List String :=
  match op with
  | .act command =>
    if host.allowed command world then
      match mode with
      | .dryRun => (⟨⟨.dryRun, none⟩, world⟩, [])
      | .simulate => (host.simulate command world, [])
      | .production =>
        if host.expired command world then (⟨⟨.timedOut, none⟩, world⟩, [])
        else (host.production command world, [command.actuator])
    else (⟨⟨.rejected, none⟩, world⟩, [])
  | other => (host.ordinary other world, [])

structure Outcome (World Result : Type) where
  value : Option Result
  world : World
  dispatches : List String

def interpret (mode : Mode) (host : Host Data World) :
    Nat → Program Data Result → World → Outcome World Result
  | _, .done value, world => ⟨some value, world, []⟩
  | 0, .request _ _, world => ⟨none, world, []⟩
  | fuel + 1, .request op next, world =>
    let (answer, sent) := step mode host op world
    let rest := interpret mode host fuel (next answer.value) answer.world
    ⟨rest.value, rest.world, sent ++ rest.dispatches⟩

def erase (outcome : Outcome World Result) : Reply World (Option Result) :=
  ⟨outcome.value, outcome.world⟩

abbrev Answers (Data World : Type) :=
  {Result : Type} → Operation Data Result → World → Reply World Result

def answersFor (mode : Mode) (host : Host Data World) : Answers Data World :=
  fun op world => (step mode host op world).1

def isAction : Operation Data Result → Bool
  | .act _ => true
  | _ => false

theorem ordinary_answers_shared (leftMode rightMode : Mode) (host : Host Data World)
    (op : Operation Data Result) (world : World) (ordinary : isAction op = false) :
    (step leftMode host op world).1 = (step rightMode host op world).1 := by
  cases op <;> simp_all [isAction, step]

/-- The one mode-free interpreter of the original tree and its continuations. -/
def fold (answers : Answers Data World) :
    Nat → Program Data Result → World → Reply World (Option Result)
  | _, .done value, world => ⟨some value, world⟩
  | 0, .request _ _, world => ⟨none, world⟩
  | fuel + 1, .request op next, world =>
    let answer := answers op world
    fold answers fuel (next answer.value) answer.world

theorem step_no_dispatch (mode : Mode) (host : Host Data World)
    (op : Operation Data Result) (world : World) (nonProduction : mode ≠ .production) :
    (step mode host op world).2 = [] := by
  cases op <;> try rfl
  case act command =>
    cases mode with
    | dryRun => cases h : host.allowed command world <;> simp [step, h]
    | simulate => cases h : host.allowed command world <;> simp [step, h]
    | production => exact False.elim (nonProduction rfl)

theorem non_production_no_dispatch (mode : Mode) (host : Host Data World)
    (fuel : Nat) (program : Program Data Result) (world : World)
    (nonProduction : mode ≠ .production) :
    (interpret mode host fuel program world).dispatches = [] := by
  induction fuel generalizing program world with
  | zero => cases program <;> rfl
  | succ fuel ih =>
    cases program with
    | done => rfl
    | request op next =>
      simp only [interpret]
      rw [step_no_dispatch mode host op world nonProduction]
      exact ih _ _

theorem dry_run_no_dispatch (host : Host Data World) (fuel : Nat)
    (program : Program Data Result) (world : World) :
    (interpret .dryRun host fuel program world).dispatches = [] :=
  non_production_no_dispatch .dryRun host fuel program world (by decide)

theorem simulation_no_dispatch (host : Host Data World) (fuel : Nat)
    (program : Program Data Result) (world : World) :
    (interpret .simulate host fuel program world).dispatches = [] :=
  non_production_no_dispatch .simulate host fuel program world (by decide)

theorem dry_action_unchanged (host : Host Data World) (command : Command Data)
    (world : World) (allowed : host.allowed command world = true) :
    step .dryRun host (.act command) world = (⟨⟨.dryRun, none⟩, world⟩, []) := by
  simp [step, allowed]

theorem handlers_interpret_same_term (mode : Mode) (host : Host Data World)
    (fuel : Nat) (program : Program Data Result) (world : World) :
    erase (interpret mode host fuel program world) =
      fold (answersFor mode host) fuel program world := by
  induction fuel generalizing program world with
  | zero => cases program <;> rfl
  | succ fuel ih =>
    cases program with
    | done => rfl
    | request op next =>
      simpa only [interpret, erase, fold, answersFor] using
        ih (next (step mode host op world).1.value) (step mode host op world).1.world

/-- Results may differ only through operation replies/state transitions, not a rewritten term. -/
theorem equal_answers_equal_results (leftMode rightMode : Mode)
    (left right : Host Data World)
    (agreement : ∀ {Result} (op : Operation Data Result) world,
      (step leftMode left op world).1 = (step rightMode right op world).1)
    (fuel : Nat) (program : Program Data Result) (world : World) :
    erase (interpret leftMode left fuel program world) =
      erase (interpret rightMode right fuel program world) := by
  have same : (answersFor leftMode left : Answers Data World) =
      (answersFor rightMode right : Answers Data World) := by
    funext Result op world
    exact agreement op world
  rw [handlers_interpret_same_term, handlers_interpret_same_term, same]

end Hypomnesis.Effects.Handlers
