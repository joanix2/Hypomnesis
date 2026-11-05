import Hypomnesis.Epistemics.Provenance

namespace Hypomnesis.Epistemics.Revision

def variables : Prov String → List String
  | .obs x => [x]
  | .zero | .one => []
  | .plus a b | .times a b => variables a ++ variables b

def containsZero : Prov String → Bool
  | .zero => true
  | .obs _ | .one => false
  | .plus a b | .times a b => containsZero a || containsZero b

def holds (p : Prov String) (withdrawn : List String) : Bool :=
  p.eval (fun x => !withdrawn.contains x)

structure Fact (Data : Type) where
  key : String
  provenance : Prov String
  data : Data

def dependencyIndex (facts : List (Fact Data)) (source : String) : List String :=
  (facts.filter (fun f => (variables f.provenance).contains source)).map (·.key)

def indexed (facts : List (Fact Data)) (withdrawn : List String) : List String :=
  withdrawn.flatMap (dependencyIndex facts)

def candidate (facts : List (Fact Data)) (withdrawn : List String) (f : Fact Data) : Bool :=
  (indexed facts withdrawn).contains f.key || containsZero f.provenance

theorem holds_unaffected (p : Prov String) (withdrawn : List String)
    (hz : containsZero p = false)
    (hn : ∀ x ∈ variables p, withdrawn.contains x = false) :
    holds p withdrawn = true := by
  induction p with
  | obs x =>
    change (!withdrawn.contains x) = true
    rw [hn x (by simp [variables])]
    rfl
  | zero => simp [containsZero] at hz
  | one => rfl
  | plus a b iha ihb =>
    simp only [containsZero, Bool.or_eq_false_iff] at hz
    have ha := iha hz.1 (fun x hx => hn x (by simp [variables, hx]))
    have hb := ihb hz.2 (fun x hx => hn x (by simp [variables, hx]))
    change (holds a withdrawn || holds b withdrawn) = true
    simp [ha, hb]
  | times a b iha ihb =>
    simp only [containsZero, Bool.or_eq_false_iff] at hz
    have ha := iha hz.1 (fun x hx => hn x (by simp [variables, hx]))
    have hb := ihb hz.2 (fun x hx => hn x (by simp [variables, hx]))
    change (holds a withdrawn && holds b withdrawn) = true
    simp [ha, hb]

theorem candidate_complete (facts : List (Fact Data)) (withdrawn : List String)
    (f : Fact Data) (hf : f ∈ facts) (h : holds f.provenance withdrawn = false) :
    candidate facts withdrawn f = true := by
  cases hz : containsZero f.provenance with
  | true => simp [candidate, hz]
  | false =>
    cases hi : (indexed facts withdrawn).contains f.key with
    | true =>
      unfold candidate
      rw [hi]
      rfl
    | false =>
      have hn : ∀ x ∈ variables f.provenance, withdrawn.contains x = false := by
        intro x hx
        cases hw : withdrawn.contains x with
        | false => rfl
        | true =>
          have hxw : x ∈ withdrawn := by simpa using hw
          have hxi : f.key ∈ dependencyIndex facts x := by
            simp only [dependencyIndex, List.mem_map, List.mem_filter]
            exact ⟨f, ⟨hf, by simpa using hx⟩, rfl⟩
          have hm : f.key ∈ indexed facts withdrawn :=
            List.mem_flatMap.mpr ⟨x, hxw, hxi⟩
          have ht : (indexed facts withdrawn).contains f.key = true := by simpa using hm
          rw [hi] at ht
          cases ht
      have ht := holds_unaffected f.provenance withdrawn hz hn
      simp [h] at ht

def invalidated (facts : List (Fact Data)) (withdrawn : List String) : List (Fact Data) :=
  facts.filter (fun f => candidate facts withdrawn f && !holds f.provenance withdrawn)

def fullInvalidated (facts : List (Fact Data)) (withdrawn : List String) : List (Fact Data) :=
  facts.filter (fun f => !holds f.provenance withdrawn)

theorem invalidated_eq_full (facts : List (Fact Data)) (withdrawn : List String) :
    invalidated facts withdrawn = fullInvalidated facts withdrawn := by
  apply List.filter_congr
  intro f hf
  cases he : holds f.provenance withdrawn with
  | false => simp [candidate_complete facts withdrawn f hf he]
  | true => simp

structure Event (Data : Type) where
  seq : Nat
  kind : String
  key : String
  detail : String
  fact : Option (Fact Data) := none
  unknown : Option (String × String) := none

structure State (Data Context : Type) where
  facts : List (Fact Data)
  unknowns : List (String × String)
  withdrawn : List String
  journal : List (Event Data)
  context : Context

def setUnknown (key detail : String) : List (String × String) → List (String × String)
  | [] => [(key, detail)]
  | (k, d) :: rest =>
    if k == key then (key, detail) :: rest else (k, d) :: setUnknown key detail rest

def retract (withdrawn : List String) (source : String) : List String :=
  if withdrawn.contains source then withdrawn else withdrawn ++ [source]

def finish (s : State Data Context) (source reason : String) (removed : List (Fact Data)) :
    State Data Context :=
  let description := "invalidée : " ++ reason
  let first : Event Data := ⟨s.journal.length + 1, "retracted", source, reason, none, none⟩
  let entries := removed.zipIdx.map fun (f, i) =>
    Event.mk (s.journal.length + 2 + i) "invalidated" f.key
      "provenance non étayée après révision" (some f) (some (f.key, description))
  { s with
    facts := s.facts.filter (fun f => !(removed.map (·.key)).contains f.key)
    unknowns := removed.foldl (fun u f => setUnknown f.key description u) s.unknowns
    withdrawn := retract s.withdrawn source
    journal := s.journal ++ (first :: entries) }

def revise_incr (s : State Data Context) (source reason : String) : Option (State Data Context) :=
  if source == "axiome" then none
  else some (finish s source reason (invalidated s.facts (retract s.withdrawn source)))

def recompute_after (s : State Data Context) (source reason : String) : Option (State Data Context) :=
  if source == "axiome" then none
  else some (finish s source reason (fullInvalidated s.facts (retract s.withdrawn source)))

theorem revise_incr_eq_full (s : State Data Context) (source reason : String) :
    revise_incr s source reason = recompute_after s source reason := by
  simp [revise_incr, recompute_after, invalidated_eq_full]

theorem journal_prefix (s out : State Data Context) (source reason : String)
    (h : revise_incr s source reason = some out) :
    ∃ extra, out.journal = s.journal ++ extra := by
  by_cases hx : source = "axiome"
  · simp [revise_incr, hx] at h
  · have he : finish s source reason
        (invalidated s.facts (retract s.withdrawn source)) = out := by
      simpa [revise_incr, hx] using h
    subst out
    exact ⟨_, rfl⟩

end Hypomnesis.Epistemics.Revision
