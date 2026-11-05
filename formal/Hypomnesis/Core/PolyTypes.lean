import Hypomnesis.Core.Syntax

/-!
# Types et schémas de rang 1 (HYP-023)

Les variables de type utilisent des indices de de Bruijn. Un schéma lie
ses `arity` premières variables ; ses autres variables viennent du contexte
extérieur. Aucun quantificateur ne se trouve à l'intérieur d'un monotype.

Ce module prépare l'extension du noyau ; il n'étend pas encore `Core.typeOf`
ni les garanties du vérificateur de certificats.
-/

namespace Hypomnesis.Core.Poly

inductive Ty where
  | var (index : Nat)
  | int
  | bool
  | float
  | string
  | unit
  | arrow (dom cod : Ty)
  | prod (fst snd : Ty)
  | data (index : Nat) (args : List Ty)
  deriving Repr

@[elab_as_elim] theorem Ty.induct {P : Ty → Prop}
    (var : ∀ i, P (.var i))
    (int : P .int) (bool : P .bool) (float : P .float)
    (string : P .string) (unit : P .unit)
    (arrow : ∀ a b, P a → P b → P (.arrow a b))
    (prod : ∀ a b, P a → P b → P (.prod a b))
    (data : ∀ d args, (∀ a ∈ args, P a) → P (.data d args)) (t : Ty) : P t :=
  Ty.rec (motive_2 := fun args => ∀ a ∈ args, P a)
    var int bool float string unit arrow prod data
    (by simp)
    (fun a args ha hargs x hx => by
      rcases List.mem_cons.mp hx with rfl | hx
      · exact ha
      · exact hargs x hx) t

mutual
  def Ty.beq : Ty → Ty → Bool
    | .var i, .var j => i == j
    | .int, .int | .bool, .bool | .float, .float | .string, .string | .unit, .unit => true
    | .arrow a b, .arrow c d => Ty.beq a c && Ty.beq b d
    | .prod a b, .prod c d => Ty.beq a c && Ty.beq b d
    | .data i args, .data j other => i == j && Ty.beqList args other
    | _, _ => false
  termination_by a b => sizeOf a + sizeOf b
  decreasing_by all_goals simp_wf <;> omega

  def Ty.beqList : List Ty → List Ty → Bool
    | [], [] => true
    | first :: rest, otherFirst :: otherRest =>
      Ty.beq first otherFirst && Ty.beqList rest otherRest
    | _, _ => false
  termination_by a b => sizeOf a + sizeOf b
  decreasing_by all_goals simp_wf <;> omega
end

instance : BEq Ty := ⟨Ty.beq⟩

private theorem beqList_eq_of_beqList_eq_true (types other : List Ty)
    (ih : ∀ type ∈ types, ∀ candidate, Ty.beq type candidate = true → type = candidate)
    (h : Ty.beqList types other = true) : types = other := by
  induction types generalizing other with
  | nil =>
    cases other <;> simp [Ty.beqList] at h ⊢
  | cons type rest ihRest =>
    cases other with
    | nil => simp [Ty.beqList] at h
    | cons candidate candidates =>
      simp only [Ty.beqList, Bool.and_eq_true] at h
      rcases h with ⟨headEq, tailEq⟩
      have head : type = candidate := ih type (by simp) candidate headEq
      subst candidate
      have tailIH : ∀ item ∈ rest, ∀ next, Ty.beq item next = true → item = next := by
        intro item member next itemEq
        exact ih item (by simp [member]) next itemEq
      have tail := ihRest candidates tailIH tailEq
      simp [tail]

theorem Ty.beq_eq_true {type other : Ty} (h : Ty.beq type other = true) : type = other := by
  induction type using Ty.induct generalizing other with
  | var index =>
    cases other with
    | var otherIndex =>
      have indices : index = otherIndex := by simpa [Ty.beq] using h
      subst otherIndex
      rfl
    | _ => simp [Ty.beq] at h
  | int =>
    cases other <;> simp [Ty.beq] at h ⊢
  | bool =>
    cases other <;> simp [Ty.beq] at h ⊢
  | float =>
    cases other <;> simp [Ty.beq] at h ⊢
  | string =>
    cases other <;> simp [Ty.beq] at h ⊢
  | unit =>
    cases other <;> simp [Ty.beq] at h ⊢
  | arrow domain codomain ihDomain ihCodomain =>
    cases other with
    | arrow otherDomain otherCodomain =>
      simp only [Ty.beq, Bool.and_eq_true] at h
      rcases h with ⟨domainEq, codomainEq⟩
      have domain := ihDomain domainEq
      have codomain := ihCodomain codomainEq
      simp [domain, codomain]
    | _ => simp [Ty.beq] at h
  | prod first second ihFirst ihSecond =>
    cases other with
    | prod otherFirst otherSecond =>
      simp only [Ty.beq, Bool.and_eq_true] at h
      rcases h with ⟨firstEq, secondEq⟩
      have first := ihFirst firstEq
      have second := ihSecond secondEq
      simp [first, second]
    | _ => simp [Ty.beq] at h
  | data index args ih =>
    cases other with
    | data otherIndex otherArgs =>
      simp only [Ty.beq, Bool.and_eq_true] at h
      rcases h with ⟨indexEq, argsEq⟩
      have index : index = otherIndex := by simpa using indexEq
      subst otherIndex
      have args := beqList_eq_of_beqList_eq_true args otherArgs ih argsEq
      simp [args]
    | _ => simp [Ty.beq] at h

private theorem beqList_refl (types : List Ty)
    (ih : ∀ type ∈ types, Ty.beq type type = true) : Ty.beqList types types = true := by
  induction types with
  | nil => simp [Ty.beqList]
  | cons type rest ihRest =>
    simp only [Ty.beqList, Bool.and_eq_true]
    constructor
    · exact ih type (by simp)
    · exact ihRest (fun item member => ih item (by simp [member]))

theorem Ty.beq_refl (type : Ty) : Ty.beq type type = true := by
  induction type using Ty.induct with
  | var => simp [Ty.beq]
  | int | bool | float | string | unit => simp [Ty.beq]
  | arrow _ _ ihDomain ihCodomain | prod _ _ ihDomain ihCodomain =>
    simp [Ty.beq, ihDomain, ihCodomain]
  | data index args ih =>
    simp only [Ty.beq, beq_self_eq_true]
    exact beqList_refl args ih

theorem Ty.beq_iff_eq (type other : Ty) : Ty.beq type other = true ↔ type = other :=
  ⟨Ty.beq_eq_true, fun h => by cases h; exact Ty.beq_refl type⟩

instance : LawfulBEq Ty where
  rfl := by
    intro type
    change Ty.beq type type = true
    exact Ty.beq_refl type
  eq_of_beq := by
    intro type other h
    change Ty.beq type other = true at h
    exact Ty.beq_eq_true h

def Ty.subst (σ : Nat → Ty) : Ty → Ty
  | .var i => σ i
  | .int => .int
  | .bool => .bool
  | .float => .float
  | .string => .string
  | .unit => .unit
  | .arrow a b => .arrow (a.subst σ) (b.subst σ)
  | .prod a b => .prod (a.subst σ) (b.subst σ)
  | .data d args => .data d (args.map (Ty.subst σ))

def Ty.rename (ρ : Nat → Nat) (t : Ty) : Ty :=
  t.subst (fun i => .var (ρ i))

@[simp] theorem Ty.subst_var (t : Ty) : t.subst Ty.var = t := by
  induction t using Ty.induct with
  | var => simp [subst]
  | int | bool | float | string | unit => simp [subst]
  | arrow _ _ ha hb | prod _ _ ha hb => simp_all [subst]
  | data d args ih =>
    simp only [subst]
    congr 1
    calc
      args.map (subst Ty.var) = args.map id := List.map_congr_left ih
      _ = args := List.map_id args

theorem Ty.subst_comp (t : Ty) (σ τ : Nat → Ty) :
    (t.subst σ).subst τ = t.subst (fun i => (σ i).subst τ) := by
  induction t using Ty.induct with
  | var => simp [subst]
  | int | bool | float | string | unit => simp [subst]
  | arrow _ _ ha hb | prod _ _ ha hb => simp_all [subst]
  | data d args ih =>
    simp only [subst, List.map_map]
    congr 1
    exact List.map_congr_left ih

@[simp] theorem Ty.rename_id (t : Ty) : t.rename id = t := by
  exact t.subst_var

theorem Ty.rename_comp (t : Ty) (ρ π : Nat → Nat) :
    (t.rename ρ).rename π = t.rename (fun i => π (ρ i)) := by
  simp [rename, subst_comp, subst]

theorem Ty.subst_rename (t : Ty) (ρ : Nat → Nat) (σ : Nat → Ty) :
    (t.rename ρ).subst σ = t.subst (fun i => σ (ρ i)) := by
  simp [rename, subst_comp, subst]

theorem Ty.rename_subst (t : Ty) (σ : Nat → Ty) (ρ : Nat → Nat) :
    (t.subst σ).rename ρ = t.subst (fun i => (σ i).rename ρ) := by
  simp [rename, subst_comp]

/-- Le nombre de paramètres de chaque déclaration de données nominale. -/
abbrev Arities := List Nat

def Ty.wellScoped (arities : Arities) (depth : Nat) : Ty → Bool
  | .var i => i < depth
  | .int | .bool | .float | .string | .unit => true
  | .arrow a b | .prod a b => a.wellScoped arities depth && b.wellScoped arities depth
  | .data d args =>
    arities[d]? == some args.length && (args.map (Ty.wellScoped arities depth)).all id

theorem Ty.subst_congr {arities : Arities} {depth : Nat} {t : Ty}
    (ht : t.wellScoped arities depth = true) (σ τ : Nat → Ty)
    (h : ∀ i, i < depth → σ i = τ i) :
    t.subst σ = t.subst τ := by
  induction t using Ty.induct with
  | var i => simp only [subst]; exact h i (by simpa [wellScoped] using ht)
  | int | bool | float | string | unit => simp [subst]
  | arrow a b ha hb | prod a b ha hb =>
    simp only [wellScoped, Bool.and_eq_true] at ht
    simp only [subst, ha ht.1, hb ht.2]
  | data d args ih =>
    simp only [wellScoped, Bool.and_eq_true, List.all_map, List.all_eq_true,
      Function.comp_def, id_eq] at ht
    simp only [subst]
    congr 1
    exact List.map_congr_left (fun a ha => ih a ha (ht.2 a ha))

theorem Ty.subst_scoped {arities : Arities} {depth target : Nat} {t : Ty}
    (ht : t.wellScoped arities depth = true) (σ : Nat → Ty)
    (hσ : ∀ i, i < depth → (σ i).wellScoped arities target = true) :
    (t.subst σ).wellScoped arities target = true := by
  induction t using Ty.induct with
  | var i => simpa [subst] using hσ i (by simpa [wellScoped] using ht)
  | int | bool | float | string | unit => simp [subst, wellScoped]
  | arrow a b ha hb | prod a b ha hb =>
    simp only [wellScoped, Bool.and_eq_true] at ht
    simp only [subst, wellScoped, Bool.and_eq_true]
    exact ⟨ha ht.1, hb ht.2⟩
  | data d args ih =>
    simp only [wellScoped, Bool.and_eq_true, List.all_map, List.all_eq_true,
      Function.comp_def, id_eq] at ht
    simp only [subst, wellScoped, List.length_map, List.all_map, Bool.and_eq_true,
      List.all_eq_true, Function.comp_def, id_eq]
    exact ⟨ht.1, fun a ha => ih a ha (ht.2 a ha)⟩

theorem Ty.rename_scoped {arities : Arities} {depth target : Nat} {t : Ty}
    (ht : t.wellScoped arities depth = true) (ρ : Nat → Nat)
    (hρ : ∀ i, i < depth → ρ i < target) :
    (t.rename ρ).wellScoped arities target = true := by
  apply Ty.subst_scoped ht
  intro i hi
  simpa [wellScoped] using hρ i hi

theorem Ty.weaken_scoped {arities : Arities} {depth target : Nat} {t : Ty}
    (ht : t.wellScoped arities depth = true) (hle : depth ≤ target) :
    t.wellScoped arities target = true := by
  simpa using Ty.rename_scoped ht id (fun _ hi => Nat.lt_of_lt_of_le hi hle)

/-- Substitution sous `count` quantificateurs : les variables liées restent
en place et les variables substituées sont affaiblies, sans capture. -/
def lift (count : Nat) (σ : Nat → Ty) (i : Nat) : Ty :=
  if i < count then .var i else (σ (i - count)).rename (fun j => j + count)

@[simp] theorem lift_bound {count i : Nat} (σ : Nat → Ty) (h : i < count) :
    lift count σ i = .var i := by
  simp [lift, h]

@[simp] theorem lift_free (count : Nat) (σ : Nat → Ty) (i : Nat) :
    lift count σ (i + count) = (σ i).rename (fun j => j + count) := by
  have h : ¬ i + count < count := by omega
  simp [lift, h]

@[simp] theorem lift_var (count : Nat) : lift count Ty.var = Ty.var := by
  funext i
  by_cases h : i < count
  · simp [lift, h]
  · simp [lift, h, Ty.rename, Ty.subst, Nat.sub_add_cancel (Nat.le_of_not_gt h)]

theorem lift_comp (count : Nat) (σ τ : Nat → Ty) (i : Nat) :
    (lift count σ i).subst (lift count τ) =
      lift count (fun j => (σ j).subst τ) i := by
  by_cases h : i < count
  · simp [lift, h, Ty.subst]
  · simp only [lift, ite_eq_right h, Ty.subst_rename, Ty.rename_subst]
    congr 1
    funext j
    exact lift_free count τ j

private theorem lift_shift_subst_free_point (binders count : Nat) (σ : Nat → Ty)
    (index : Nat) :
    (lift binders (fun i => .var (i + count)) (index + binders)).subst
        (lift binders (lift count σ)) =
      (lift binders σ (index + binders)).subst
        (lift binders (fun i => .var (i + count))) := by
  simp only [lift_free, Ty.subst_rename]
  have h3 : ¬ index + count < count := by omega
  simp [lift, h3, Ty.rename, Ty.subst, Nat.add_assoc]
  change ((σ index).rename (fun i => i + count)).rename
      (fun i => i + binders) =
    (σ index).rename (fun i => i + (count + binders))
  rw [Ty.rename_comp]
  congr 1
  funext i
  omega

private theorem lift_shift_subst_point (binders count : Nat) (σ : Nat → Ty)
    (index : Nat) :
    (lift binders (fun i => .var (i + count)) index).subst
        (lift binders (lift count σ)) =
      (lift binders σ index).subst
        (lift binders (fun i => .var (i + count))) := by
  by_cases h : index < binders
  · simp [lift, h, Ty.subst]
  · have hdecomp : index = index - binders + binders := by omega
    rw [hdecomp]
    exact lift_shift_subst_free_point binders count σ (index - binders)

theorem lift_scoped {arities : Arities} {count depth target : Nat}
    (σ : Nat → Ty)
    (hσ : ∀ i, i < depth → (σ i).wellScoped arities target = true)
    {i : Nat} (hi : i < count + depth) :
    (lift count σ i).wellScoped arities (count + target) = true := by
  by_cases h : i < count
  · simp only [lift_bound σ h, Ty.wellScoped]
    exact decide_eq_true (by omega)
  · simp only [lift, ite_eq_right h]
    apply Ty.rename_scoped (hσ (i - count) (by omega))
    intro j hj
    omega

structure Scheme where
  arity : Nat
  body : Ty
  deriving Repr

def Scheme.wellScoped (arities : Arities) (depth : Nat) (s : Scheme) : Bool :=
  s.body.wellScoped arities (s.arity + depth)

def Scheme.subst (σ : Nat → Ty) (s : Scheme) : Scheme :=
  ⟨s.arity, s.body.subst (lift s.arity σ)⟩

def Scheme.weaken (count : Nat) (s : Scheme) : Scheme :=
  s.subst fun i => .var (i + count)

@[simp] theorem Scheme.subst_var (s : Scheme) : s.subst Ty.var = s := by
  cases s
  simp [subst]

theorem Scheme.subst_comp (s : Scheme) (σ τ : Nat → Ty) :
    (s.subst σ).subst τ = s.subst (fun i => (σ i).subst τ) := by
  simp only [subst, Ty.subst_comp]
  congr 2
  funext i
  exact lift_comp s.arity σ τ i

theorem Scheme.weaken_subst (s : Scheme) (count : Nat) (σ : Nat → Ty) :
    (s.weaken count).subst (lift count σ) = (s.subst σ).weaken count := by
  cases s with
  | mk arity body =>
    change (⟨arity,
      (body.subst (lift arity (fun i => .var (i + count)))).subst
        (lift arity (lift count σ))⟩ : Scheme) =
      ⟨arity,
        (body.subst (lift arity σ)).subst
          (lift arity (fun i => .var (i + count)))⟩
    congr 1
    rw [Ty.subst_comp, Ty.subst_comp]
    congr 1
    funext i
    exact lift_shift_subst_point arity count σ i

theorem Scheme.subst_closed {arities : Arities} {s : Scheme}
    (hs : s.wellScoped arities 0 = true) (σ : Nat → Ty) :
    s.subst σ = s := by
  cases s with
  | mk arity body =>
    change (⟨arity, body.subst (lift arity σ)⟩ : Scheme) = ⟨arity, body⟩
    congr 1
    have hbody : body.wellScoped arities arity = true := by
      simpa [Scheme.wellScoped] using hs
    calc
      body.subst (lift arity σ) = body.subst Ty.var :=
        Ty.subst_congr hbody (lift arity σ) Ty.var (by
          intro index hindex
          simp [lift_bound, hindex])
      _ = body := Ty.subst_var body

theorem Scheme.subst_scoped {arities : Arities} {depth target : Nat}
    {s : Scheme} (hs : s.wellScoped arities depth = true) (σ : Nat → Ty)
    (hσ : ∀ i, i < depth → (σ i).wellScoped arities target = true) :
    (s.subst σ).wellScoped arities target = true :=
  Ty.subst_scoped hs (lift s.arity σ) (fun _ hi => lift_scoped σ hσ hi)

theorem Scheme.weaken_scoped {arities : Arities} {depth count : Nat}
    {s : Scheme} (hs : s.wellScoped arities depth = true) :
    (s.weaken count).wellScoped arities (depth + count) = true := by
  apply Scheme.subst_scoped hs
  intro i hi
  simp only [Ty.wellScoped]
  exact decide_eq_true (by omega)

/-- Instancier retire les variables liées ; les arguments sont dans le
contexte extérieur et ne sont donc pas affaiblis. -/
def instantiateSubst (args : List Ty) (i : Nat) : Ty :=
  match args[i]? with
  | some t => t
  | none => .var (i - args.length)

@[simp] theorem instantiateSubst_outer (args : List Ty) (i : Nat) :
    instantiateSubst args (i + args.length) = .var i := by
  simp [instantiateSubst]

theorem instantiateSubst_map_bound (args : List Ty) (σ : Nat → Ty)
    {i : Nat} (hi : i < args.length) :
    instantiateSubst (args.map (Ty.subst σ)) i = (args[i]).subst σ := by
  simp [instantiateSubst, hi]

theorem Ty.instantiate_rename (t : Ty) (args : List Ty) :
    (t.rename (fun i => i + args.length)).subst (instantiateSubst args) = t := by
  simp only [subst_rename, instantiateSubst_outer]
  exact t.subst_var

def Scheme.instantiate (s : Scheme) (args : List Ty) : Option Ty :=
  if args.length = s.arity then some (s.body.subst (instantiateSubst args)) else none

theorem instantiateSubst_scoped {arities : Arities} {depth : Nat} {args : List Ty}
    (ha : ∀ a ∈ args, a.wellScoped arities depth = true)
    {i : Nat} (hi : i < args.length + depth) :
    (instantiateSubst args i).wellScoped arities depth = true := by
  unfold instantiateSubst
  split
  · rename_i a h
    exact ha a (List.mem_of_getElem? h)
  · rename_i h
    have hn : args.length ≤ i := by simpa using List.getElem?_eq_none_iff.mp h
    simp only [Ty.wellScoped]
    exact decide_eq_true (by omega)

theorem Scheme.instantiate_scoped {arities : Arities} {depth : Nat} {s : Scheme}
    (hs : s.wellScoped arities depth = true) {args : List Ty}
    (ha : ∀ a ∈ args, a.wellScoped arities depth = true)
    {t : Ty} (h : s.instantiate args = some t) :
    t.wellScoped arities depth = true := by
  unfold instantiate at h
  split at h
  · rename_i length
    cases h
    exact Ty.subst_scoped hs _ (fun i hi => instantiateSubst_scoped ha (by
      change i < s.arity + depth at hi
      omega))
  · cases h

theorem Scheme.instantiate_subst (s : Scheme) (args : List Ty) (σ : Nat → Ty) :
    (s.subst σ).instantiate (args.map (Ty.subst σ)) =
      (s.instantiate args).map (Ty.subst σ) := by
  by_cases length : args.length = s.arity
  · simp only [instantiate, subst, List.length_map, length, ↓reduceIte, Option.map_some,
      Ty.subst_comp]
    congr 2
    funext i
    by_cases hi : i < s.arity
    · have hargs : i < args.length := by omega
      simp only [lift_bound σ hi, Ty.subst, instantiateSubst_map_bound args σ hargs]
      simp [instantiateSubst, List.getElem?_eq_getElem hargs]
    · have hnone : args[i]? = none := List.getElem?_eq_none (by omega)
      simp only [lift, ite_eq_right hi, instantiateSubst, hnone]
      rw [← length]
      simpa only [List.length_map, Ty.subst] using
        Ty.instantiate_rename (σ (i - args.length)) (args.map (Ty.subst σ))
  · simp [instantiate, subst, length]

abbrev TyEnv := List Scheme

def TyEnv.wellScoped (arities : Arities) (depth : Nat) (env : TyEnv) : Bool :=
  env.all (Scheme.wellScoped arities depth)

def TyEnv.subst (σ : Nat → Ty) (env : TyEnv) : TyEnv :=
  env.map (Scheme.subst σ)

def TyEnv.weaken (count : Nat) (env : TyEnv) : TyEnv :=
  env.map (Scheme.weaken count)

theorem TyEnv.weaken_subst (env : TyEnv) (count : Nat) (σ : Nat → Ty) :
    (env.weaken count).subst (lift count σ) = (env.subst σ).weaken count := by
  induction env with
  | nil => rfl
  | cons scheme env ih =>
    simp [TyEnv.weaken, TyEnv.subst, Scheme.weaken_subst]

def TyEnv.instantiate (env : TyEnv) (index : Nat) (args : List Ty) : Option Ty :=
  (env[index]?).bind fun scheme => scheme.instantiate args

theorem TyEnv.subst_scoped {arities : Arities} {depth target : Nat}
    {env : TyEnv} (henv : env.wellScoped arities depth = true) (σ : Nat → Ty)
    (hσ : ∀ i, i < depth → (σ i).wellScoped arities target = true) :
    (env.subst σ).wellScoped arities target = true := by
  simp only [TyEnv.wellScoped, TyEnv.subst, List.all_map, List.all_eq_true] at *
  intro scheme hscheme
  exact Scheme.subst_scoped (henv scheme hscheme) σ hσ

theorem TyEnv.weaken_scoped {arities : Arities} {depth count : Nat}
    {env : TyEnv} (henv : env.wellScoped arities depth = true) :
    (env.weaken count).wellScoped arities (depth + count) = true := by
  simp only [TyEnv.wellScoped, TyEnv.weaken, List.all_map, List.all_eq_true] at *
  intro scheme hscheme
  exact Scheme.weaken_scoped (henv scheme hscheme)

theorem TyEnv.instantiate_scoped {arities : Arities} {depth : Nat}
    {env : TyEnv} (henv : env.wellScoped arities depth = true)
    {index : Nat} {args : List Ty} (hargs : ∀ a ∈ args, a.wellScoped arities depth = true)
    {t : Ty} (h : env.instantiate index args = some t) :
    t.wellScoped arities depth = true := by
  unfold TyEnv.instantiate at h
  cases hindex : env[index]? with
  | none => simp [hindex] at h
  | some scheme =>
    have hscheme := List.all_eq_true.mp henv scheme (List.mem_of_getElem? hindex)
    have hinst : scheme.instantiate args = some t := by
      simpa [hindex] using h
    exact Scheme.instantiate_scoped hscheme hargs hinst

theorem TyEnv.instantiate_subst (env : TyEnv) (index : Nat) (args : List Ty)
    (σ : Nat → Ty) :
    (env.subst σ).instantiate index (args.map (Ty.subst σ)) =
      (env.instantiate index args).map (Ty.subst σ) := by
  induction env generalizing index with
  | nil => simp [TyEnv.instantiate, TyEnv.subst]
  | cons scheme env ih =>
    cases index with
    | zero => simp [TyEnv.instantiate, TyEnv.subst, Scheme.instantiate_subst]
    | succ index => exact ih index

def mono (t : Ty) : Scheme := ⟨0, t⟩

@[simp] theorem mono_instantiate (t : Ty) : (mono t).instantiate [] = some t := by
  have h : instantiateSubst [] = Ty.var := by
    funext i
    simp [instantiateSubst]
  simp [Scheme.instantiate, mono, h]

structure DataDecl where
  parameters : Nat
  constructors : List Ty
  deriving Repr

abbrev Signature := List DataDecl

def Signature.arities (sig : Signature) : Arities :=
  sig.map DataDecl.parameters

def Signature.wellFormed (sig : Signature) : Bool :=
  sig.all fun decl =>
    (decl.constructors.map (Ty.wellScoped sig.arities decl.parameters)).all id

def Signature.constructorType (sig : Signature) (d c : Nat) (args : List Ty) : Option Ty := do
  let decl ← sig[d]?
  let payload ← decl.constructors[c]?
  (Scheme.mk decl.parameters payload).instantiate args

theorem Signature.constructorType_subst {sig : Signature}
    (hsig : sig.wellFormed = true) (d c : Nat) (args : List Ty) (σ : Nat → Ty) :
    (sig.constructorType d c args).map (Ty.subst σ) =
      sig.constructorType d c (args.map (Ty.subst σ)) := by
  unfold Signature.constructorType
  change Option.map (Ty.subst σ)
      (sig[d]?.bind fun decl =>
        decl.constructors[c]?.bind fun payload =>
          (Scheme.mk decl.parameters payload).instantiate args) =
    sig[d]?.bind fun decl =>
      decl.constructors[c]?.bind fun payload =>
        (Scheme.mk decl.parameters payload).instantiate (args.map (Ty.subst σ))
  rw [Option.map_bind]
  apply Option.bind_congr
  intro decl hdeclLookup
  change Option.map (Ty.subst σ)
      (decl.constructors[c]?.bind fun payload =>
        (Scheme.mk decl.parameters payload).instantiate args) =
    decl.constructors[c]?.bind fun payload =>
      (Scheme.mk decl.parameters payload).instantiate (args.map (Ty.subst σ))
  rw [Option.map_bind]
  apply Option.bind_congr
  intro payload hpayloadLookup
  have hsig' : ∀ declaration ∈ sig,
      (declaration.constructors.map
        (Ty.wellScoped sig.arities declaration.parameters)).all id = true := by
    simpa [Signature.wellFormed] using hsig
  have hdecl := hsig' decl (List.mem_of_getElem? hdeclLookup)
  have hp := (List.all_eq_true.mp hdecl) (payload.wellScoped sig.arities decl.parameters)
    (List.mem_map.mpr ⟨payload, List.mem_of_getElem? hpayloadLookup, rfl⟩)
  have hscheme : (Scheme.mk decl.parameters payload).wellScoped sig.arities 0 = true := by
    change payload.wellScoped sig.arities (decl.parameters + 0) = true
    simpa using hp
  rw [← Scheme.subst_closed hscheme σ]
  exact (Scheme.instantiate_subst ⟨decl.parameters, payload⟩ args σ).symm

theorem Signature.constructorType_scoped {sig : Signature}
    (hs : sig.wellFormed = true) {depth d c : Nat} {args : List Ty}
    (ha : ∀ a ∈ args, a.wellScoped sig.arities depth = true)
    {t : Ty} (h : sig.constructorType d c args = some t) :
    t.wellScoped sig.arities depth = true := by
  unfold constructorType at h
  cases hd : sig[d]? with
  | none => simp [hd] at h
  | some decl =>
    cases hc : decl.constructors[c]? with
    | none => simp [hd, hc] at h
    | some payload =>
      simp only [hd] at h
      change (decl.constructors[c]?.bind fun p =>
        (Scheme.mk decl.parameters p).instantiate args) = some t at h
      simp only [hc] at h
      change (Scheme.mk decl.parameters payload).instantiate args = some t at h
      have hdecl := List.all_eq_true.mp hs decl (List.mem_of_getElem? hd)
      simp only [List.all_map, List.all_eq_true, Function.comp_def, id_eq] at hdecl
      apply Scheme.instantiate_scoped (s := ⟨decl.parameters, payload⟩) _ ha h
      exact Ty.weaken_scoped (hdecl payload (List.mem_of_getElem? hc)) (by
        change decl.parameters ≤ decl.parameters + depth
        omega)

/-- Inclusion des types historiques, sans changement du noyau monomorphe. -/
def Ty.ofCore : Core.Ty → Ty
  | .int => .int
  | .bool => .bool
  | .float => .float
  | .string => .string
  | .unit => .unit
  | .arrow a b => .arrow (ofCore a) (ofCore b)
  | .prod a b => .prod (ofCore a) (ofCore b)
  | .data d => .data d []

def Ty.erase : Ty → Core.Ty
  | .var _ => .unit
  | .int => .int
  | .bool => .bool
  | .float => .float
  | .string => .string
  | .unit => .unit
  | .arrow a b => .arrow a.erase b.erase
  | .prod a b => .prod a.erase b.erase
  | .data d _ => .data d

@[simp] theorem Ty.erase_ofCore (t : Core.Ty) : (Ty.ofCore t).erase = t := by
  induction t <;> simp [Ty.ofCore, Ty.erase, *]

theorem Ty.ofCore_subst (t : Core.Ty) (σ : Nat → Ty) :
    (ofCore t).subst σ = ofCore t := by
  induction t with
  | int | bool | float | string | unit | data => simp [ofCore, subst]
  | arrow a b ha hb | prod a b ha hb => simp [ofCore, subst, ha, hb]

theorem Ty.closed_subst {arities : Arities} {t : Ty}
    (ht : t.wellScoped arities 0 = true) (σ : Nat → Ty) :
    t.subst σ = t := by
  calc
    t.subst σ = t.subst Ty.var := Ty.subst_congr ht σ Ty.var (by omega)
    _ = t := t.subst_var

end Hypomnesis.Core.Poly
