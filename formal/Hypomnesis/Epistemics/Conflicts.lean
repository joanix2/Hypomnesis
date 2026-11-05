import Hypomnesis.Epistemics.Revision

namespace Hypomnesis.Epistemics.Conflicts

open Revision

structure Invariant (Data : Type) where
  name : String
  keys : List String
  accepts : List (Fact Data) → Bool

structure Theory (Data : Type) where
  functional : List String
  invariants : List (Invariant Data)

inductive Report (Data : Type) where
  | functional (key : String) (facts : List (Fact Data))
  | invariant (rule : Invariant Data) (facts : List (Fact Data))

def live (facts : List (Fact Data)) (withdrawn : List String) : List (Fact Data) :=
  facts.filter (fun f => holds f.provenance withdrawn)

def group (facts : List (Fact Data)) (key : String) : List (Fact Data) :=
  facts.filter (fun f => f.key == key)

def choices (facts : List (Fact Data)) : List String → List (List (Fact Data))
  | [] => [[]]
  | key :: keys =>
    (group facts key).flatMap (fun f => (choices facts keys).map (fun fs => f :: fs))

def different [DecidableEq Value] (view : Data → Value) : List (Fact Data) → Bool
  | [] => false
  | f :: rest => rest.any (fun g => decide (view f.data ≠ view g.data))

def scan [DecidableEq Value] (view : Data → Value) (theory : Theory Data)
    (facts : List (Fact Data)) (withdrawn : List String) : List (Report Data) :=
  let active := live facts withdrawn
  theory.functional.flatMap (fun key =>
    let fs := group active key
    if different view fs then [Report.functional key fs] else []) ++
  theory.invariants.flatMap (fun rule =>
    (choices active rule.keys).flatMap (fun fs =>
      if rule.accepts fs then [] else [Report.invariant rule fs]))

def Aligned (facts : List (Fact Data)) (keys : List String) (fs : List (Fact Data)) : Prop :=
  fs.map (·.key) = keys ∧ ∀ f ∈ fs, f ∈ facts

def Compatible (view : Data → Value) (theory : Theory Data)
    (facts : List (Fact Data)) : Prop :=
  (∀ key ∈ theory.functional, ∀ f ∈ facts, ∀ g ∈ facts,
    f.key = key → g.key = key → view f.data = view g.data) ∧
  (∀ rule ∈ theory.invariants, ∀ fs, Aligned facts rule.keys fs → rule.accepts fs = true)

theorem group_member (h : f ∈ group facts key) : f ∈ facts ∧ f.key = key := by
  simpa [group] using h

theorem choices_aligned (h : fs ∈ choices facts keys) : Aligned facts keys fs := by
  induction keys generalizing fs with
  | nil =>
    simp [choices] at h
    subst fs
    simp [Aligned]
  | cons key keys ih =>
    simp only [choices, List.mem_flatMap, List.mem_map] at h
    obtain ⟨f, hf, tail, ht, he⟩ := h
    subst fs
    have hg := group_member hf
    have ha := ih ht
    constructor
    · simp [hg.2, ha.1]
    · intro g hmem
      simp only [List.mem_cons] at hmem
      cases hmem with
      | inl he => simpa [he] using hg.1
      | inr hm => exact ha.2 g hm

theorem different_witness [DecidableEq Value] (view : Data → Value)
    (h : different view fs = true) :
    ∃ f ∈ fs, ∃ g ∈ fs, view f.data ≠ view g.data := by
  cases fs with
  | nil => simp [different] at h
  | cons f rest =>
    simp only [different, List.any_eq_true, decide_eq_true_eq] at h
    obtain ⟨g, hg, hn⟩ := h
    exact ⟨f, by simp, g, by simp [hg], hn⟩

theorem no_false_conflict [DecidableEq Value] (view : Data → Value)
    (theory : Theory Data) (facts : List (Fact Data)) (withdrawn : List String)
    (report : Report Data) (h : report ∈ scan view theory facts withdrawn) :
    ¬ Compatible view theory (live facts withdrawn) := by
  intro compatible
  simp only [scan, List.mem_append, List.mem_flatMap] at h
  cases h with
  | inl h =>
    obtain ⟨key, hk, hr⟩ := h
    split at hr
    next hd =>
      have hw := different_witness view hd
      obtain ⟨f, hf, g, hg, hn⟩ := hw
      have hfm := group_member hf
      have hgm := group_member hg
      exact hn (compatible.1 key hk f hfm.1 g hgm.1 hfm.2 hgm.2)
    next => simp at hr
  | inr h =>
    obtain ⟨rule, hr, fs, hf, hrep⟩ := h
    split at hrep
    next => simp at hrep
    next hn =>
      have ht := compatible.2 rule hr fs (choices_aligned hf)
      simp [ht] at hn

end Hypomnesis.Epistemics.Conflicts
