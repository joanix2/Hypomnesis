/-!
# Provenance en semi-anneau et révision

Formalise le §6.4 de `docs/architecture/m3-metalangage.md` (d'après Green,
Karvounarakis, Tannen, *Provenance semirings*, PODS 2007) :

* la provenance d'une conclusion est un terme libre sur les identifiants
  d'observations : `⊗` (`times`) pour des prémisses utilisées conjointement,
  `⊕` (`plus`) pour des dérivations alternatives ;
* toute lecture (grade de support, validité booléenne, confiance, coût) est
  l'évaluation de ce terme dans un semi-anneau ;
* **réviser** (retirer ou remplacer des observations) est une substitution, et
  l'évaluation commute avec la substitution : recalculer après révision
  revient à évaluer avec la valuation révisée (cahier des charges §7.3, H4) ;
* sur le treillis de support, l'évaluation est **monotone** : dégrader le
  support d'une observation ne peut pas améliorer celui d'une conclusion.
-/

namespace Hypomnesis.Epistemics

/-- Terme de provenance libre sur des identifiants d'observations `X`. -/
inductive Prov (X : Type) where
  | obs (x : X)
  | zero
  | one
  | plus (a b : Prov X)
  | times (a b : Prov X)
  deriving Repr

/-- Opérations d'un semi-anneau (les lois ne servent pas aux énoncés ci-dessous). -/
class SemiringOps (K : Type) where
  zero : K
  one : K
  add : K → K → K
  mul : K → K → K

namespace Prov

variable {X Y K : Type}

def eval [SemiringOps K] (ν : X → K) : Prov X → K
  | obs x => ν x
  | zero => SemiringOps.zero
  | one => SemiringOps.one
  | plus a b => SemiringOps.add (a.eval ν) (b.eval ν)
  | times a b => SemiringOps.mul (a.eval ν) (b.eval ν)

/-- Substitution des observations (révision). -/
def subst (σ : X → Prov Y) : Prov X → Prov Y
  | obs x => σ x
  | zero => zero
  | one => one
  | plus a b => plus (a.subst σ) (b.subst σ)
  | times a b => times (a.subst σ) (b.subst σ)

/-- L'évaluation commute avec la substitution. -/
theorem eval_subst [SemiringOps K] (σ : X → Prov Y) (ν : Y → K) (p : Prov X) :
    (p.subst σ).eval ν = p.eval (fun x => (σ x).eval ν) := by
  induction p with
  | obs x => rfl
  | zero => rfl
  | one => rfl
  | plus a b iha ihb => simp [subst, eval, iha, ihb]
  | times a b iha ihb => simp [subst, eval, iha, ihb]

/-- Retrait de l'observation `x₀` : elle est remplacée par `0`. -/
def retract [DecidableEq X] (x₀ : X) : X → Prov X :=
  fun x => if x = x₀ then zero else obs x

end Prov

/-! ## Lecture booléenne : la conclusion tient-elle encore ? -/

instance : SemiringOps Bool where
  zero := false
  one := true
  add := (· || ·)
  mul := (· && ·)

/-- **Révision.** Après retrait de `x₀`, une conclusion tient si et seulement si
elle tient lorsque `x₀` est considérée fausse : aucun recalcul global n'est
nécessaire, ni aucune autre observation affectée. -/
theorem holds_after_retract {X : Type} [DecidableEq X] (p : Prov X) (x₀ : X) (ν : X → Bool) :
    (p.subst (Prov.retract x₀)).eval ν = p.eval (fun x => if x = x₀ then false else ν x) := by
  rw [Prov.eval_subst]
  congr 1
  funext x
  by_cases h : x = x₀ <;> simp [Prov.retract, h, Prov.eval, SemiringOps.zero]

/-- Une conclusion qui ne mentionne pas `x₀` n'est pas affectée par son retrait. -/
def Prov.mentions {X : Type} (x₀ : X) : Prov X → Prop
  | .obs x => x = x₀
  | .zero | .one => False
  | .plus a b | .times a b => a.mentions x₀ ∨ b.mentions x₀

theorem retract_unrelated {X K : Type} [DecidableEq X] [SemiringOps K]
    (p : Prov X) (x₀ : X) (ν : X → K) (h : ¬ p.mentions x₀) :
    (p.subst (Prov.retract x₀)).eval ν = p.eval ν := by
  induction p with
  | obs x =>
    simp [Prov.mentions] at h
    simp [Prov.subst, Prov.retract, h]
  | zero => rfl
  | one => rfl
  | plus a b iha ihb =>
    simp [Prov.mentions, not_or] at h
    simp [Prov.subst, Prov.eval, iha h.1, ihb h.2]
  | times a b iha ihb =>
    simp [Prov.mentions, not_or] at h
    simp [Prov.subst, Prov.eval, iha h.1, ihb h.2]

/-! ## Treillis de support (axe « support » des statuts, note M3 §4.3) -/

inductive Support where
  | observed | estimated | defaulted | hypothesis | unsupported
  deriving DecidableEq, Repr

/-- Rang : plus il est élevé, moins le support est fort. -/
def Support.rank : Support → Nat
  | .observed => 0 | .estimated => 1 | .defaulted => 2 | .hypothesis => 3 | .unsupported => 4

/-- Usage conjoint : le support le plus faible l'emporte. -/
def Support.weakest (a b : Support) : Support := if a.rank ≤ b.rank then b else a
/-- Dérivations alternatives : la meilleure l'emporte. -/
def Support.strongest (a b : Support) : Support := if a.rank ≤ b.rank then a else b

instance : SemiringOps Support where
  zero := .unsupported
  one := .observed
  add := Support.strongest
  mul := Support.weakest

theorem Support.rank_weakest (a b : Support) : (a.weakest b).rank = max a.rank b.rank := by
  unfold weakest; split <;> omega

theorem Support.rank_strongest (a b : Support) : (a.strongest b).rank = min a.rank b.rank := by
  unfold strongest; split <;> omega

/-- **Monotonie du support.** Si chaque observation est au moins aussi bien
supportée sous `ν` que sous `μ`, toute conclusion l'est aussi. -/
theorem support_mono {X : Type} (p : Prov X) (ν μ : X → Support)
    (h : ∀ x, (ν x).rank ≤ (μ x).rank) : (p.eval ν).rank ≤ (p.eval μ).rank := by
  induction p with
  | obs x => exact h x
  | zero => exact Nat.le_refl _
  | one => exact Nat.le_refl _
  | plus a b iha ihb =>
    show (Support.strongest _ _).rank ≤ (Support.strongest _ _).rank
    rw [Support.rank_strongest, Support.rank_strongest]; omega
  | times a b iha ihb =>
    show (Support.weakest _ _).rank ≤ (Support.weakest _ _).rank
    rw [Support.rank_weakest, Support.rank_weakest]; omega

/-- Une conclusion n'est jamais mieux supportée que l'une de ses prémisses
conjointes : dériver d'une estimation donne au mieux une estimation. -/
theorem conjunction_no_stronger {X : Type} (a b : Prov X) (ν : X → Support) :
    (a.eval ν).rank ≤ ((Prov.times a b).eval ν).rank := by
  show _ ≤ (Support.weakest _ _).rank
  rw [Support.rank_weakest]; omega

end Hypomnesis.Epistemics
