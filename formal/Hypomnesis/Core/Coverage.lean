import Hypomnesis.Core.Soundness

/-!
# Exhaustivité par spécialisation de matrices

Le résultat `none` signale un budget épuisé, jamais une preuve de couverture.
Les gardes sont éliminées par l'appelant avant la construction de la matrice.
-/

namespace Hypomnesis.Core.Coverage

abbrev Row := List Pat
abbrev Matrix := List Row

def Matches : Row → List Val → Prop
  | [], [] => True
  | p :: ps, v :: vs => (∃ bindings, matchPat p v = some bindings) ∧ Matches ps vs
  | _, _ => False

def Covers (matrix : Matrix) (values : List Val) : Prop :=
  ∃ row ∈ matrix, Matches row values

def wild : Pat → Bool
  | .wild | .var => true
  | _ => false

def defaults (matrix : Matrix) : Matrix :=
  matrix.filterMap fun row =>
    match row with
    | p :: ps => if wild p then some ps else none
    | [] => none

inductive Head where
  | boolean (value : Bool)
  | pair
  | ctor (index : Nat)
  deriving DecidableEq, Repr

def arguments : Head → Pat → Option Row
  | .boolean _, .wild | .boolean _, .var => some []
  | .boolean b, .bool c => if b = c then some [] else none
  | .pair, .wild | .pair, .var => some [.wild, .wild]
  | .pair, .pair a b => some [a, b]
  | .ctor _, .wild | .ctor _, .var => some [.wild]
  | .ctor c, .ctor d p => if c = d then some [p] else none
  | _, _ => none

def specialize (head : Head) (matrix : Matrix) : Matrix :=
  matrix.filterMap fun row =>
    match row with
    | p :: ps => (arguments head p).map (· ++ ps)
    | [] => none

def branches (sig : Sig) : Ty → Option (List (Head × Ctx))
  | .bool => some [(.boolean false, []), (.boolean true, [])]
  | .prod a b => some [(.pair, [a, b])]
  | .data d => (sig[d]?).map fun cs => cs.zipIdx.map fun (t, c) => (.ctor c, [t])
  | _ => none

def allCovered : List (Option Bool) → Option Bool
  | [] => some true
  | some true :: rest => allCovered rest
  | some false :: _ => some false
  | none :: _ => none

def present (head : Head) (matrix : Matrix) : Bool :=
  matrix.any fun row =>
    match row with
    | p :: _ => !wild p && (arguments head p).isSome
    | [] => false

def check (sig : Sig) : Nat → Matrix → Ctx → Option Bool
  | 0, _, _ => none
  | _ + 1, matrix, [] => some (matrix.any List.isEmpty)
  | fuel + 1, matrix, t :: ts =>
    match check sig fuel (defaults matrix) ts with
    | some true => some true
    | defaultResult =>
      match branches sig t with
      | none => defaultResult
      | some heads =>
        if heads.all (fun (h, _) => present h matrix) then
          allCovered (heads.map fun (h, args) =>
            check sig fuel (specialize h matrix) (args ++ ts))
        else defaultResult

def exhaustive (sig : Sig) (fuel : Nat) (t : Ty) (patterns : List Pat) : Option Bool :=
  check sig fuel (patterns.map fun p => [p]) [t]

theorem wild_matches {p : Pat} (h : wild p = true) (v : Val) :
    ∃ bindings, matchPat p v = some bindings := by
  cases p <;> simp_all [wild, matchPat]

theorem defaults_sound {matrix : Matrix} {v : Val} {vs : List Val}
    (h : Covers (defaults matrix) vs) : Covers matrix (v :: vs) := by
  obtain ⟨row, member, matched⟩ := h
  obtain ⟨original, originalMember, selected⟩ := List.mem_filterMap.mp member
  cases original with
  | nil => simp at selected
  | cons p ps =>
    simp only at selected
    split at selected
    next hp =>
      cases selected
      exact ⟨_, originalMember, wild_matches hp v, matched⟩
    next => contradiction

def build : Head → List Val → Option Val
  | .boolean b, [] => some (.bool b)
  | .pair, [a, b] => some (.pair a b)
  | .ctor c, [v] => some (.con c v)
  | _, _ => none

theorem arguments_sound {head : Head} {p : Pat} {ps rest : Row} {args tail : List Val}
    {v : Val} (ha : arguments head p = some ps) (hb : build head args = some v)
    (hm : Matches (ps ++ rest) (args ++ tail)) :
    Matches (p :: rest) (v :: tail) := by
  cases head with
  | boolean b =>
    cases args with
    | cons => simp [build] at hb
    | nil =>
      simp only [build, Option.some.injEq] at hb
      subst v
      cases p <;> simp_all [arguments, Matches, matchPat]
  | pair =>
    cases args with
    | nil => simp [build] at hb
    | cons a args =>
      cases args with
      | nil => simp [build] at hb
      | cons b args =>
        cases args with
        | cons => simp [build] at hb
        | nil =>
          simp only [build, Option.some.injEq] at hb
          subst v
          cases p <;> simp only [arguments] at ha <;> try contradiction
          all_goals cases ha
          all_goals simp only [List.cons_append, List.nil_append, Matches] at hm ⊢
          all_goals first
            | exact ⟨⟨_, rfl⟩, hm.2.2⟩
            | obtain ⟨⟨xs, hx⟩, ⟨ys, hy⟩, ht⟩ := hm
              exact ⟨⟨ys ++ xs, by simp [matchPat, hx, hy]⟩, ht⟩
  | ctor c =>
    cases args with
    | nil => simp [build] at hb
    | cons a args =>
      cases args with
      | cons => simp [build] at hb
      | nil =>
        simp only [build, Option.some.injEq] at hb
        subst v
        cases p <;> simp only [arguments] at ha <;> try contradiction
        all_goals try (split at ha <;> try contradiction)
        all_goals cases ha
        all_goals simp_all [Matches, matchPat]

theorem specialize_sound {head : Head} {matrix : Matrix} {args tail : List Val}
    {v : Val} (hb : build head args = some v)
    (h : Covers (specialize head matrix) (args ++ tail)) :
    Covers matrix (v :: tail) := by
  obtain ⟨row, member, matched⟩ := h
  obtain ⟨original, originalMember, selected⟩ := List.mem_filterMap.mp member
  cases original with
  | nil => simp at selected
  | cons p rest =>
    simp only at selected
    obtain ⟨ps, hp, heq⟩ := Option.map_eq_some_iff.mp selected
    subst row
    exact ⟨_, originalMember, arguments_sound hp hb matched⟩

theorem allCovered_sound {results : List (Option Bool)}
    (h : allCovered results = some true) :
    ∀ result ∈ results, result = some true := by
  induction results with
  | nil => simp
  | cons result rest ih =>
    cases result with
    | none => simp [allCovered] at h
    | some b =>
      cases b with
      | false => simp [allCovered] at h
      | true =>
        simp only [allCovered] at h
        intro result member
        rcases List.mem_cons.mp member with rfl | member
        · rfl
        · exact ih h result member

theorem branches_complete {sig : Sig} {t : Ty} {v : Val}
    {heads : List (Head × Ctx)} (hb : branches sig t = some heads)
    (hv : ValTy sig v t) :
    ∃ head args types, (head, types) ∈ heads ∧
      EnvTy sig args types ∧ build head args = some v := by
  cases hv <;> simp only [branches] at hb <;> try contradiction
  case bool b =>
    cases hb
    exact ⟨.boolean b, [], [], by cases b <;> simp, EnvTy.nil, rfl⟩
  case pair a b ta tb ha hb' =>
    cases hb
    exact ⟨.pair, [a, b], [ta, tb], by simp,
      .cons ha (.cons hb' .nil), rfl⟩
  case con d c cs ta v hsig hctor hv =>
    simp only [hsig, Option.map_some, Option.some.injEq] at hb
    subst heads
    refine ⟨.ctor c, [v], [ta], ?_, .cons hv .nil, rfl⟩
    apply List.mem_map.mpr
    refine ⟨(ta, c), ?_, rfl⟩
    exact List.mk_mem_zipIdx_iff_getElem?.mpr hctor

theorem check_sound {sig : Sig} {fuel : Nat} {matrix : Matrix} {types : Ctx}
    (h : check sig fuel matrix types = some true) :
    ∀ {values}, EnvTy sig values types → Covers matrix values := by
  induction fuel generalizing matrix types with
  | zero => simp [check] at h
  | succ fuel ih =>
    intro values typed
    cases typed with
    | nil =>
      simp only [check, Option.some.injEq, List.any_eq_true] at h
      obtain ⟨row, member, empty⟩ := h
      have : row = [] := List.isEmpty_iff.mp empty
      subst row
      exact ⟨[], member, trivial⟩
    | @cons v t vs ts hv hvs =>
      simp only [check] at h
      split at h
      next hd => exact defaults_sound (ih hd hvs)
      next hd =>
        split at h
        next => exact defaults_sound (ih h hvs)
        next heads hb =>
          split at h
          next =>
            obtain ⟨head, args, types, member, hargs, built⟩ := branches_complete hb hv
            have branch := allCovered_sound h _ (List.mem_map.mpr ⟨(head, types), member, rfl⟩)
            exact specialize_sound built (ih branch (hargs.append hvs))
          next => exact defaults_sound (ih h hvs)

theorem exhaustive_sound {sig : Sig} {fuel : Nat} {t : Ty} {patterns : List Pat}
    (h : exhaustive sig fuel t patterns = some true) {v : Val} (hv : ValTy sig v t) :
    ∃ p ∈ patterns, ∃ bindings, matchPat p v = some bindings := by
  obtain ⟨row, member, matched⟩ := check_sound h (.cons hv .nil)
  obtain ⟨p, patternMember, eq⟩ := List.mem_map.mp member
  subst row
  exact ⟨p, patternMember, matched.1⟩

structure Arm where
  pattern : Pat
  guarded : Bool
  body : Expr
  deriving Repr

def unguarded (arms : List Arm) : List Pat :=
  arms.filterMap fun arm => if arm.guarded then none else some arm.pattern

def select (guard : Arm → List Val → Bool) (v : Val) :
    List Arm → Option (Arm × List Val)
  | [] => none
  | arm :: rest =>
    match matchPat arm.pattern v with
    | none => select guard v rest
    | some bindings =>
      if !arm.guarded || guard arm bindings then some (arm, bindings)
      else select guard v rest

theorem unguarded_member {p : Pat} {arms : List Arm} (h : p ∈ unguarded arms) :
    ∃ arm ∈ arms, arm.guarded = false ∧ arm.pattern = p := by
  obtain ⟨arm, member, selected⟩ := List.mem_filterMap.mp h
  split at selected
  · contradiction
  · exact ⟨arm, member, by simpa using ‹¬arm.guarded = true›, Option.some.inj selected⟩

theorem select_complete {guard : Arm → List Val → Bool} {v : Val} {arms : List Arm}
    (h : ∃ arm ∈ arms, arm.guarded = false ∧
      ∃ bindings, matchPat arm.pattern v = some bindings) :
    ∃ chosen bindings, select guard v arms = some (chosen, bindings) := by
  induction arms with
  | nil => simp at h
  | cons arm rest ih =>
    obtain ⟨covered, member, unguarded, bindings, matched⟩ := h
    rcases List.mem_cons.mp member with rfl | member
    · exact ⟨covered, bindings, by simp [select, matched, unguarded]⟩
    · have tail := ih ⟨covered, member, unguarded, bindings, matched⟩
      simp only [select]
      cases hm : matchPat arm.pattern v with
      | none => exact tail
      | some bs =>
        simp only at *
        split
        · exact ⟨arm, bs, rfl⟩
        · exact tail

theorem guarded_exhaustive_selects {sig : Sig} {fuel : Nat} {t : Ty}
    {arms : List Arm}
    (h : exhaustive sig fuel t (unguarded arms) = some true)
    {v : Val} (hv : ValTy sig v t) (guard : Arm → List Val → Bool) :
    ∃ chosen bindings, select guard v arms = some (chosen, bindings) := by
  obtain ⟨p, member, bindings, matched⟩ := exhaustive_sound h hv
  obtain ⟨arm, member, hg, hp⟩ := unguarded_member member
  exact select_complete ⟨arm, member, hg, bindings, by simpa [hp] using matched⟩

theorem select_sound {guard : Arm → List Val → Bool} {v : Val} {arms : List Arm}
    {chosen : Arm} {bindings : List Val}
    (h : select guard v arms = some (chosen, bindings)) :
    chosen ∈ arms ∧ matchPat chosen.pattern v = some bindings ∧
      (!chosen.guarded || guard chosen bindings) = true := by
  induction arms with
  | nil => simp [select] at h
  | cons arm rest ih =>
    simp only [select] at h
    cases hm : matchPat arm.pattern v with
    | none =>
      simp only [hm] at h
      obtain ⟨member, matched, accepted⟩ := ih h
      exact ⟨List.mem_cons_of_mem _ member, matched, accepted⟩
    | some vs =>
      simp only [hm] at h
      split at h
      next hg =>
        cases h
        exact ⟨by simp, hm, hg⟩
      next =>
        obtain ⟨member, matched, accepted⟩ := ih h
        exact ⟨List.mem_cons_of_mem _ member, matched, accepted⟩

def caseChain (index : Nat) (result : Ty) : List (Pat × Expr) → Expr
  | [] => .fail result
  | (pattern, body) :: rest => .case (.var index) pattern body (caseChain index result rest)

theorem caseChain_no_matchFail {budget index : Nat} {result : Ty}
    {v : Val} {env : List Val} {arms : List (Pat × Expr)}
    (covered : ∃ p ∈ arms.map Prod.fst, ∃ bs, matchPat p v = some bs)
    (lookup : env[index]? = some v)
    (bodies : ∀ arm ∈ arms, ∀ bs, matchPat arm.1 v = some bs →
      ∀ fuel, eval fuel (bs ++ env) arm.2 ≠ .matchFail) :
    eval budget env (caseChain index result arms) ≠ .matchFail := by
  induction budget generalizing arms with
  | zero => simp [eval]
  | succ budget ih =>
    cases arms with
    | nil => simp at covered
    | cons arm rest =>
      cases budget with
      | zero => simp [caseChain, eval, Res.bind]
      | succ budget =>
        simp only [caseChain, eval, lookup, Res.bind]
        cases hm : matchPat arm.1 v with
        | some bs =>
          exact bodies arm (by simp) bs hm (budget + 1)
        | none =>
          apply ih
          · obtain ⟨p, member, bs, matched⟩ := covered
            rcases List.mem_cons.mp member with hp | member
            · simp only [hp, hm] at matched
              contradiction
            · exact ⟨p, member, bs, matched⟩
          · intro a ha
            exact bodies a (List.mem_cons_of_mem _ ha)

theorem exhaustive_caseChain_no_matchFail {sig : Sig} {fuel budget index : Nat}
    {t result : Ty} {v : Val} {env : List Val} {arms : List (Pat × Expr)}
    (h : exhaustive sig fuel t (arms.map Prod.fst) = some true)
    (hv : ValTy sig v t) (lookup : env[index]? = some v)
    (bodies : ∀ arm ∈ arms, ∀ bs, matchPat arm.1 v = some bs →
      ∀ n, eval n (bs ++ env) arm.2 ≠ .matchFail) :
    eval budget env (caseChain index result arms) ≠ .matchFail :=
  caseChain_no_matchFail (exhaustive_sound h hv) lookup bodies

end Hypomnesis.Core.Coverage
