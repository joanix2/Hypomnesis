import Hypomnesis.Core.PolyTypes

/-! # Régressions calculées des portées et instanciations de types (HYP-023)

Le schéma de map ci-dessous est uniquement un test de représentation des
types. Il ne prouve pas encore le typage du corps de `List.map` du prélude.
-/

namespace Hypomnesis.Core.Poly.Examples

def listSig : Signature :=
  [⟨1, [.unit, .prod (.var 0) (.data 0 [.var 0])]⟩]

def list (a : Ty) : Ty := .data 0 [a]

def mapScheme : Scheme :=
  ⟨2, .arrow (.arrow (.var 0) (.var 1)) (.arrow (list (.var 0)) (list (.var 1)))⟩

def mapEnv : TyEnv := [mapScheme]

def outerEnv : TyEnv := [Scheme.mk 1 (.prod (.var 0) (.var 1))]

theorem list_signature_valid : listSig.wellFormed = true := by
  simp [listSig, Signature.wellFormed, Signature.arities, Ty.wellScoped]

theorem map_scheme_scoped : mapScheme.wellScoped listSig.arities 0 = true := by
  simp [mapScheme, Scheme.wellScoped, listSig, list, Signature.arities, Ty.wellScoped]

theorem generic_list_tail :
    listSig.constructorType 0 1 [.var 0] = some (.prod (.var 0) (list (.var 0))) := by
  simp [Signature.constructorType, listSig, list, Scheme.instantiate, Ty.subst,
    instantiateSubst]

theorem map_int_bool :
    mapScheme.instantiate [.int, .bool] =
      some (.arrow (.arrow .int .bool) (.arrow (list .int) (list .bool))) := by
  simp [mapScheme, list, Scheme.instantiate, Ty.subst, instantiateSubst]

theorem map_wrong_arity : mapScheme.instantiate [.int] = none := by
  simp [mapScheme, Scheme.instantiate]

theorem map_environment_int_bool :
    mapEnv.instantiate 0 [.int, .bool] =
      some (.arrow (.arrow .int .bool) (.arrow (list .int) (list .bool))) := by
  simp [mapEnv, mapScheme, list, TyEnv.instantiate, Scheme.instantiate, Ty.subst,
    instantiateSubst]

theorem map_environment_wrong_arity : mapEnv.instantiate 0 [.int] = none := by
  simp [mapEnv, mapScheme, TyEnv.instantiate, Scheme.instantiate]

theorem environment_instantiation_retains_outer_scope :
    TyEnv.instantiate ([Scheme.mk 1 (.prod (.var 0) (.var 1))] : TyEnv) 0 [.bool] =
      some (.prod .bool (.var 0)) := by
  simp [TyEnv.instantiate, Scheme.instantiate, Ty.subst, instantiateSubst]

theorem environment_instantiation_commutes_with_substitution
    (σ : Nat → Ty) :
    (mapEnv.subst σ).instantiate 0 ([.int, .bool].map (Ty.subst σ)) =
      (mapEnv.instantiate 0 [.int, .bool]).map (Ty.subst σ) :=
  TyEnv.instantiate_subst mapEnv 0 [.int, .bool] σ

theorem environment_weakening_preserves_scope :
    outerEnv.wellScoped listSig.arities 1 = true ∧
      (outerEnv.weaken 2).wellScoped listSig.arities 3 = true := by
  constructor
  · simp [outerEnv, TyEnv.wellScoped, Scheme.wellScoped, Ty.wellScoped,
      listSig, Signature.arities]
  · exact TyEnv.weaken_scoped (by
      simp [outerEnv, TyEnv.wellScoped, Scheme.wellScoped, Ty.wellScoped,
        listSig, Signature.arities])

theorem environment_weakening_retains_outer_variables :
    TyEnv.instantiate (outerEnv.weaken 2) 0 [.var 1] =
      some (.prod (.var 1) (.var 2)) := by
  simp [outerEnv, TyEnv.instantiate, TyEnv.weaken, Scheme.weaken, Scheme.subst,
      Scheme.instantiate, Ty.subst, Ty.rename, lift, instantiateSubst]

theorem unbound_variable_rejected : (Ty.var 1).wellScoped listSig.arities 1 = false := by
  simp [Ty.wellScoped]

theorem wrong_data_arity_rejected :
    (Ty.data 0 [.int, .bool]).wellScoped listSig.arities 0 = false := by
  simp [listSig, Signature.arities, Ty.wellScoped]

theorem unknown_data_rejected :
    (Ty.data 1 [.int]).wellScoped listSig.arities 0 = false := by
  simp [listSig, Signature.arities, Ty.wellScoped]

theorem malformed_constructor_rejected :
    Signature.wellFormed [⟨1, [.var 1]⟩] = false := by
  simp [Signature.wellFormed, Ty.wellScoped]

theorem wrong_constructor_arguments : listSig.constructorType 0 1 [] = none := by
  simp [Signature.constructorType, listSig, Scheme.instantiate]

theorem unknown_constructor : listSig.constructorType 0 2 [.int] = none := by
  simp [Signature.constructorType, listSig]

theorem substitution_does_not_capture :
    (Scheme.mk 1 (.prod (.var 0) (.var 1))).subst (fun _ => list (.var 0)) =
      Scheme.mk 1 (.prod (.var 0) (list (.var 1))) := by
  simp [Scheme.subst, Ty.subst, lift, Ty.rename, list]

theorem instantiation_retains_outer_scope :
    (Scheme.mk 1 (.prod (.var 0) (.var 1))).instantiate [.bool] =
      some (.prod .bool (.var 0)) := by
  simp [Scheme.instantiate, Ty.subst, instantiateSubst]

end Hypomnesis.Core.Poly.Examples
