import Hypomnesis.Core.PolySyntax

/-! # Jugement et vérificateur de types polymorphes (HYP-023) -/

namespace Hypomnesis.Core.Poly

def PatTy (sig : Signature) (pat : Pat) (type : Ty) : Option (List Ty) :=
  match pat, type with
  | .wild, _ => some []
  | .var, _ => some [type]
  | .int _, .int => some []
  | .bool _, .bool => some []
  | .float _, .float => some []
  | .string _, .string => some []
  | .pair first second, .prod firstType secondType =>
    match PatTy sig first firstType, PatTy sig second secondType with
    | some firstBindings, some secondBindings => some (secondBindings ++ firstBindings)
    | _, _ => none
  | .ctor ctor arg, .data data args =>
    match sig.constructorType data ctor args with
    | some payload => PatTy sig arg payload
    | none => none
  | _, _ => none

private def typesScoped (sig : Signature) (depth : Nat) (types : List Ty) : Bool :=
  types.all fun type => type.wellScoped sig.arities depth

private def typeOfAux (sig : Signature) (depth : Nat) (env : TyEnv) : Expr → Option Ty
  | .var index args =>
    if typesScoped sig depth args then env.instantiate index args else none
  | .int _ => some .int
  | .bool _ => some .bool
  | .float _ => some .float
  | .string _ => some .string
  | .unit => some .unit
  | .lam domain body =>
    if domain.wellScoped sig.arities depth then
      (typeOfAux sig depth (mono domain :: env) body).map (.arrow domain)
    else none
  | .fix domain codomain body =>
    if domain.wellScoped sig.arities depth && codomain.wellScoped sig.arities depth then
      match typeOfAux sig depth (mono domain :: mono (.arrow domain codomain) :: env) body with
      | some result => if result == codomain then some (.arrow domain codomain) else none
      | none => none
    else none
  | .app fn arg =>
    match typeOfAux sig depth env fn, typeOfAux sig depth env arg with
    | some (.arrow domain codomain), some argType =>
      if domain == argType then some codomain else none
    | _, _ => none
  | .letE scheme value body =>
    if scheme.wellScoped sig.arities depth then
      match typeOfAux sig (depth + scheme.arity) (env.weaken scheme.arity) value with
      | some valueType =>
        if valueType == scheme.body then typeOfAux sig depth (scheme :: env) body else none
      | none => none
    else none
  | .ite condition thenBranch elseBranch =>
    match typeOfAux sig depth env condition,
      typeOfAux sig depth env thenBranch, typeOfAux sig depth env elseBranch with
    | some .bool, some thenType, some elseType =>
      if thenType == elseType then some thenType else none
    | _, _, _ => none
  | .pair first second =>
    match typeOfAux sig depth env first, typeOfAux sig depth env second with
    | some firstType, some secondType => some (.prod firstType secondType)
    | _, _ => none
  | .fst expr =>
    match typeOfAux sig depth env expr with
    | some (.prod firstType _) => some firstType
    | _ => none
  | .snd expr =>
    match typeOfAux sig depth env expr with
    | some (.prod _ secondType) => some secondType
    | _ => none
  | .binop op lhs rhs =>
    match typeOfAux sig depth env lhs, typeOfAux sig depth env rhs with
    | some lhsType, some rhsType =>
      let domain := Ty.ofCore op.domain
      if lhsType == domain && rhsType == domain then some (Ty.ofCore op.result) else none
    | _, _ => none
  | .construct data ctor args arg =>
    if typesScoped sig depth args then
      match sig.constructorType data ctor args, typeOfAux sig depth env arg with
      | some payload, some argType =>
        if payload == argType then some (.data data args) else none
      | _, _ => none
    else none
  | .case scrutinee pat onMatch onFail =>
    match typeOfAux sig depth env scrutinee with
    | some scrutineeType =>
      match PatTy sig pat scrutineeType with
      | some bindings =>
        let inner := bindings.map mono ++ env
        if TyEnv.wellScoped sig.arities depth inner then
          match typeOfAux sig depth inner onMatch, typeOfAux sig depth env onFail with
          | some matchType, some failType =>
            if matchType == failType then some matchType else none
          | _, _ => none
        else none
      | none => none
    | none => none
  | .fail type =>
    if type.wellScoped sig.arities depth then some type else none
  | .raise type message =>
    if type.wellScoped sig.arities depth then
      match typeOfAux sig depth env message with
      | some .string => some type
      | _ => none
    else none

/-- Le vérificateur public refuse les signatures et contextes mal formés
avant de vérifier le terme. -/
def typeOf (sig : Signature) (depth : Nat) (env : TyEnv) (expr : Expr) : Option Ty :=
  if sig.wellFormed && env.wellScoped sig.arities depth then
    typeOfAux sig depth env expr
  else none

inductive HasType (sig : Signature) : Nat → TyEnv → Expr → Ty → Prop where
  | var {index args scheme type} :
      env[index]? = some scheme → scheme.instantiate args = some type →
      (args.all fun t => t.wellScoped sig.arities depth) = true →
      HasType sig depth env (.var index args) type
  | int {value} : HasType sig depth env (.int value) .int
  | bool {value} : HasType sig depth env (.bool value) .bool
  | float {value} : HasType sig depth env (.float value) .float
  | string {value} : HasType sig depth env (.string value) .string
  | unit : HasType sig depth env .unit .unit
  | lam {domain body codomain} :
      domain.wellScoped sig.arities depth = true →
      HasType sig depth (mono domain :: env) body codomain →
      HasType sig depth env (.lam domain body) (.arrow domain codomain)
  | fix {domain codomain body} :
      domain.wellScoped sig.arities depth = true →
      codomain.wellScoped sig.arities depth = true →
      HasType sig depth (mono domain :: mono (.arrow domain codomain) :: env) body codomain →
      HasType sig depth env (.fix domain codomain body) (.arrow domain codomain)
  | app {fn arg domain codomain} :
      HasType sig depth env fn (.arrow domain codomain) →
      HasType sig depth env arg domain →
      HasType sig depth env (.app fn arg) codomain
  | letE {scheme value body type} :
      scheme.wellScoped sig.arities depth = true →
      HasType sig (depth + scheme.arity) (TyEnv.weaken scheme.arity env) value scheme.body →
      HasType sig depth (scheme :: env) body type →
      HasType sig depth env (.letE scheme value body) type
  | ite {condition thenBranch elseBranch type} :
      HasType sig depth env condition .bool →
      HasType sig depth env thenBranch type →
      HasType sig depth env elseBranch type →
      HasType sig depth env (.ite condition thenBranch elseBranch) type
  | pair {first second firstType secondType} :
      HasType sig depth env first firstType →
      HasType sig depth env second secondType →
      HasType sig depth env (.pair first second) (.prod firstType secondType)
  | fst {expr firstType secondType} :
      HasType sig depth env expr (.prod firstType secondType) →
      HasType sig depth env (.fst expr) firstType
  | snd {expr firstType secondType} :
      HasType sig depth env expr (.prod firstType secondType) →
      HasType sig depth env (.snd expr) secondType
  | binop {op lhs rhs} :
      HasType sig depth env lhs (Ty.ofCore op.domain) →
      HasType sig depth env rhs (Ty.ofCore op.domain) →
      HasType sig depth env (.binop op lhs rhs) (Ty.ofCore op.result)
  | construct {data ctor args payload arg} :
      sig.constructorType data ctor args = some payload →
      (args.all fun t => t.wellScoped sig.arities depth) = true →
      HasType sig depth env arg payload →
      HasType sig depth env (.construct data ctor args arg) (.data data args)
  | case {scrutinee pat onMatch onFail scrutineeType bindings resultType} :
      HasType sig depth env scrutinee scrutineeType →
      PatTy sig pat scrutineeType = some bindings →
      TyEnv.wellScoped sig.arities depth (bindings.map mono ++ env) = true →
      HasType sig depth (bindings.map mono ++ env) onMatch resultType →
      HasType sig depth env onFail resultType →
      HasType sig depth env (.case scrutinee pat onMatch onFail) resultType
  | fail {type} :
      type.wellScoped sig.arities depth = true →
      HasType sig depth env (.fail type) type
  | raise {type message} :
      type.wellScoped sig.arities depth = true →
      HasType sig depth env message .string →
      HasType sig depth env (.raise type message) type

theorem PatTy.subst {sig : Signature} (hsig : sig.wellFormed = true)
    {pat : Pat} {type : Ty} {bindings : List Ty} (σ : Nat → Ty)
    (hpat : PatTy sig pat type = some bindings) :
    PatTy sig pat (type.subst σ) = some (bindings.map (Ty.subst σ)) := by
  induction pat generalizing type bindings with
  | wild =>
    simp [PatTy] at hpat
    subst bindings
    simp [PatTy]
  | var =>
    simp [PatTy] at hpat
    subst bindings
    simp [PatTy]
  | int value =>
    cases type with
    | int =>
      simp [PatTy] at hpat
      subst bindings
      simp [PatTy, Ty.subst]
    | _ => simp [PatTy] at hpat
  | bool value =>
    cases type with
    | bool =>
      simp [PatTy] at hpat
      subst bindings
      simp [PatTy, Ty.subst]
    | _ => simp [PatTy] at hpat
  | float value =>
    cases type with
    | float =>
      simp [PatTy] at hpat
      subst bindings
      simp [PatTy, Ty.subst]
    | _ => simp [PatTy] at hpat
  | string value =>
    cases type with
    | string =>
      simp [PatTy] at hpat
      subst bindings
      simp [PatTy, Ty.subst]
    | _ => simp [PatTy] at hpat
  | pair first second ihFirst ihSecond =>
    cases type with
    | prod firstType secondType =>
      simp only [PatTy] at hpat
      cases hfirst : PatTy sig first firstType with
      | none => simp [hfirst] at hpat
      | some firstBindings =>
        cases hsecond : PatTy sig second secondType with
        | none => simp [hfirst, hsecond] at hpat
        | some secondBindings =>
          simp only [hfirst, hsecond, Option.some.injEq] at hpat
          subst bindings
          simp only [PatTy, Ty.subst]
          rw [ihFirst hfirst, ihSecond hsecond]
          simp
    | _ => simp [PatTy] at hpat
  | ctor ctor arg ih =>
    cases type with
    | data data args =>
      simp only [PatTy] at hpat
      cases hconstructor : sig.constructorType data ctor args with
      | none => simp [hconstructor] at hpat
      | some payload =>
        simp only [hconstructor] at hpat
        simp only [PatTy, Ty.subst]
        rw [← Signature.constructorType_subst hsig]
        rw [hconstructor]
        exact ih hpat
    | _ => simp [PatTy] at hpat

private theorem lift_zero (σ : Nat → Ty) : lift 0 σ = σ := by
  funext i
  change Ty.rename id (σ i) = σ i
  exact Ty.rename_id (σ i)

@[simp] private theorem mono_subst (t : Ty) (σ : Nat → Ty) :
    (mono t).subst σ = mono (t.subst σ) := by
  simp [mono, Scheme.subst, lift_zero]

private theorem monoEnv_subst (bindings : List Ty) (env : TyEnv) (σ : Nat → Ty) :
    TyEnv.subst σ (bindings.map mono ++ env) =
      (bindings.map fun t => mono (t.subst σ)) ++ env.subst σ := by
  simp [TyEnv.subst, List.map_map]

theorem HasType.subst {sig : Signature} {depth : Nat} {env : TyEnv}
    {expr : Expr} {type : Ty} (hsig : sig.wellFormed = true)
    (h : HasType sig depth env expr type) (σ : Nat → Ty) (target : Nat)
    (hσ : ∀ i, i < depth → (σ i).wellScoped sig.arities target = true) :
    HasType sig target (env.subst σ) (expr.subst σ) (type.subst σ) := by
  induction h generalizing σ target with
  | @var env' _depth index args scheme type hindex hinstantiate hargs =>
    have hindex' : (env'.subst σ)[index]? = some (scheme.subst σ) := by
      simpa [TyEnv.subst] using congrArg (Option.map (Scheme.subst σ)) hindex
    have hargs' :
        (args.map (Ty.subst σ)).all
          (fun t => t.wellScoped sig.arities target) = true := by
      apply List.all_eq_true.mpr
      intro t ht
      obtain ⟨original, horiginal, rfl⟩ := List.mem_map.mp ht
      exact Ty.subst_scoped (List.all_eq_true.mp hargs original horiginal) σ hσ
    refine .var hindex' ?_ hargs'
    rw [Scheme.instantiate_subst]
    simp [hinstantiate]
  | @int value =>
    simp only [Expr.subst, Ty.subst]
    exact .int
  | @bool value =>
    simp only [Expr.subst, Ty.subst]
    exact .bool
  | @float value =>
    simp only [Expr.subst, Ty.subst]
    exact .float
  | @string value =>
    simp only [Expr.subst, Ty.subst]
    exact .string
  | unit =>
    simp only [Expr.subst, Ty.subst]
    exact .unit
  | @lam depth' env' domain body codomain hdomain _body ih =>
    simp only [Expr.subst, Ty.subst]
    refine .lam ?_ ?_
    · exact Ty.subst_scoped hdomain σ hσ
    · simpa [TyEnv.subst, Scheme.subst, mono, lift, lift_zero, Ty.subst] using
        ih σ target hσ
  | @fix depth' env' domain codomain body hdomain hcodomain _body ih =>
    simp only [Expr.subst, Ty.subst]
    refine .fix ?_ ?_ ?_
    · exact Ty.subst_scoped hdomain σ hσ
    · exact Ty.subst_scoped hcodomain σ hσ
    · simpa [TyEnv.subst, Scheme.subst, mono, lift, lift_zero, Ty.subst] using
        ih σ target hσ
  | @app _depth env' fn arg domain codomain _fn _arg ihFn ihArg =>
    simp only [Expr.subst]
    have hfn : HasType sig target (env'.subst σ) (fn.subst σ)
        (.arrow (domain.subst σ) (codomain.subst σ)) := by
      simpa [Ty.subst] using ihFn σ target hσ
    have harg : HasType sig target (env'.subst σ) (arg.subst σ)
        (domain.subst σ) := by
      simpa [Ty.subst] using ihArg σ target hσ
    exact .app hfn harg
  | @letE depth' env' scheme value body type hscheme _value _body ihValue ihBody =>
    have hσ' : ∀ i, i < depth' + scheme.arity →
        (lift scheme.arity σ i).wellScoped sig.arities (target + scheme.arity) = true := by
      intro i hi
      simpa [Nat.add_comm] using lift_scoped σ hσ (by omega)
    simp only [Expr.subst]
    refine .letE ?_ ?_ ?_
    · exact Scheme.subst_scoped hscheme σ hσ
    · simpa [Scheme.subst, TyEnv.weaken_subst] using
        ihValue (lift scheme.arity σ) (target + scheme.arity) hσ'
    · simpa [TyEnv.subst, Scheme.subst] using ihBody σ target hσ
  | @ite _depth env' condition thenBranch elseBranch type _condition _then _else
      ihCondition ihThen ihElse =>
    simp only [Expr.subst]
    refine .ite ?_ ?_ ?_
    · simpa [Ty.subst] using ihCondition σ target hσ
    · simpa [Ty.subst] using ihThen σ target hσ
    · simpa [Ty.subst] using ihElse σ target hσ
  | @pair _depth env' first second firstType secondType _first _second ihFirst ihSecond =>
    simp only [Expr.subst]
    simpa [Ty.subst] using
      HasType.pair (ihFirst σ target hσ) (ihSecond σ target hσ)
  | @fst _depth env' expr firstType secondType _expr ih =>
    simp only [Expr.subst]
    have hexpr : HasType sig target (env'.subst σ) (expr.subst σ)
        (.prod (firstType.subst σ) (secondType.subst σ)) := by
      simpa [Ty.subst] using ih σ target hσ
    exact .fst hexpr
  | @snd _depth env' expr firstType secondType _expr ih =>
    simp only [Expr.subst]
    have hexpr : HasType sig target (env'.subst σ) (expr.subst σ)
        (.prod (firstType.subst σ) (secondType.subst σ)) := by
      simpa [Ty.subst] using ih σ target hσ
    exact .snd hexpr
  | @binop _depth env' op lhs rhs _lhs _rhs ihLhs ihRhs =>
    simp only [Expr.subst]
    have hLhs := ihLhs σ target hσ
    have hRhs := ihRhs σ target hσ
    have hLhs' : HasType sig target (env'.subst σ) (lhs.subst σ) (Ty.ofCore op.domain) := by
      simpa [Ty.ofCore_subst] using hLhs
    have hRhs' : HasType sig target (env'.subst σ) (rhs.subst σ) (Ty.ofCore op.domain) := by
      simpa [Ty.ofCore_subst] using hRhs
    simpa [Ty.ofCore_subst] using HasType.binop hLhs' hRhs'
  | @construct _depth env' data ctor args payload arg hconstructor hargs _arg ihArg =>
    have hargs' :
        (args.map (Ty.subst σ)).all
          (fun t => t.wellScoped sig.arities target) = true := by
      apply List.all_eq_true.mpr
      intro t ht
      obtain ⟨original, horiginal, rfl⟩ := List.mem_map.mp ht
      exact Ty.subst_scoped (List.all_eq_true.mp hargs original horiginal) σ hσ
    have hconstructor' :
        sig.constructorType data ctor (args.map (Ty.subst σ)) =
          some (payload.subst σ) := by
      rw [← Signature.constructorType_subst hsig, hconstructor]
      rfl
    simp only [Expr.subst]
    simpa [Ty.subst] using .construct hconstructor' hargs' (ihArg σ target hσ)
  | @case _depth env' scrutinee pattern onMatch onFail scrutineeType bindings resultType
      _scrutinee hpattern hcontext _onMatch _onFail ihScrutinee ihMatch ihFail =>
    have hpattern' := PatTy.subst hsig σ hpattern
    have hcontext' :
        TyEnv.wellScoped sig.arities target
          ((bindings.map fun t => mono (t.subst σ)) ++ env'.subst σ) = true := by
      have hscoped := TyEnv.subst_scoped hcontext σ hσ
      rw [monoEnv_subst] at hscoped
      simpa [TyEnv.wellScoped] using hscoped
    simp only [Expr.subst]
    refine .case (ihScrutinee σ target hσ) hpattern' (by
      simpa [List.map_map, Function.comp_def] using hcontext') ?_
      (ihFail σ target hσ)
    simpa [monoEnv_subst, List.map_map, Function.comp_def] using ihMatch σ target hσ
  | @fail _depth env' type htype =>
    simp only [Expr.subst]
    exact .fail (Ty.subst_scoped htype σ hσ)
  | @raise _depth env' type message htype _message ihMessage =>
    simp only [Expr.subst]
    refine .raise (Ty.subst_scoped htype σ hσ) ?_
    simpa [Ty.subst] using ihMessage σ target hσ

theorem typeOfAux_sound {sig : Signature} {depth : Nat} {env : TyEnv}
    {expr : Expr} {type : Ty}
    (h : typeOfAux sig depth env expr = some type) :
    HasType sig depth env expr type := by
  induction expr generalizing depth env type with
  | var index args =>
    simp only [typeOfAux] at h
    split at h
    · rename_i hargs
      have hinst : env.instantiate index args = some type := h
      cases hindex : env[index]? with
      | none => simp [TyEnv.instantiate, hindex] at hinst
      | some scheme =>
        have hscheme : scheme.instantiate args = some type := by
          simpa [TyEnv.instantiate, hindex] using hinst
        exact .var hindex hscheme hargs
    · simp at h
  | int value => simp only [typeOfAux, Option.some.injEq] at h; subst type; exact .int
  | bool value => simp only [typeOfAux, Option.some.injEq] at h; subst type; exact .bool
  | float value => simp only [typeOfAux, Option.some.injEq] at h; subst type; exact .float
  | string value => simp only [typeOfAux, Option.some.injEq] at h; subst type; exact .string
  | unit => simp only [typeOfAux, Option.some.injEq] at h; subst type; exact .unit
  | lam domain body ih =>
    simp only [typeOfAux] at h
    split at h
    · rename_i hdomain
      simp only [Option.map_eq_some_iff] at h
      obtain ⟨codomain, hbody, rfl⟩ := h
      exact .lam hdomain (ih hbody)
    · simp at h
  | fix domain codomain body ih =>
    simp only [typeOfAux] at h
    split at h
    · rename_i hscoped
      simp only [Bool.and_eq_true] at hscoped
      rcases hscoped with ⟨hdomain, hcodomain⟩
      split at h
      · rename_i result hbody
        split at h
        · rename_i resultEq
          have resultEq' : result = codomain :=
            (Ty.beq_iff_eq result codomain).mp resultEq
          subst result
          simp at h
          subst type
          exact .fix hdomain hcodomain (ih hbody)
        · simp at h
      · simp at h
    · simp at h
  | app fn arg ihFn ihArg =>
    simp only [typeOfAux] at h
    split at h
    · rename_i domain codomain argType hfn harg
      split at h
      · rename_i domainEq
        have domainEq' : domain = argType :=
          (Ty.beq_iff_eq domain argType).mp domainEq
        subst argType
        simp at h
        subst type
        exact .app (ihFn hfn) (ihArg harg)
      · simp at h
    · simp at h
  | letE scheme value body ihValue ihBody =>
    simp only [typeOfAux] at h
    split at h
    · rename_i hscheme
      split at h
      · rename_i valueType hvalue
        split at h
        · rename_i valueEq
          have valueEq' : valueType = scheme.body :=
            (Ty.beq_iff_eq valueType scheme.body).mp valueEq
          subst valueType
          exact .letE hscheme (ihValue hvalue) (ihBody h)
        · simp at h
      · simp at h
    · simp at h
  | ite condition thenBranch elseBranch ihCondition ihThen ihElse =>
    simp only [typeOfAux] at h
    split at h
    · rename_i conditionType thenType elseType hcondition hthen helse
      split at h
      · rename_i typesEq
        have typesEq' : thenType = elseType :=
          (Ty.beq_iff_eq thenType elseType).mp typesEq
        subst elseType
        simp at h
        subst type
        exact .ite (ihCondition hcondition) (ihThen hthen) (ihElse helse)
      · simp at h
    · simp at h
  | pair first second ihFirst ihSecond =>
    simp only [typeOfAux] at h
    split at h
    · rename_i firstType secondType hfirst hsecond
      simp at h
      subst type
      exact .pair (ihFirst hfirst) (ihSecond hsecond)
    · simp at h
  | fst expr ih =>
    simp only [typeOfAux] at h
    split at h
    · rename_i firstType secondType hexpr
      simp at h
      subst type
      exact .fst (ih hexpr)
    · simp at h
  | snd expr ih =>
    simp only [typeOfAux] at h
    split at h
    · rename_i firstType secondType hexpr
      simp at h
      subst type
      exact .snd (ih hexpr)
    · simp at h
  | binop op lhs rhs ihLhs ihRhs =>
    simp only [typeOfAux] at h
    split at h
    · rename_i lhsType rhsType hlhs hrhs
      split at h
      · rename_i typesEq
        simp only [Bool.and_eq_true] at typesEq
        rcases typesEq with ⟨lhsEq, rhsEq⟩
        have lhsEq' : lhsType = Ty.ofCore op.domain :=
          (Ty.beq_iff_eq lhsType (Ty.ofCore op.domain)).mp lhsEq
        have rhsEq' : rhsType = Ty.ofCore op.domain :=
          (Ty.beq_iff_eq rhsType (Ty.ofCore op.domain)).mp rhsEq
        subst lhsType
        subst rhsType
        simp at h
        subst type
        exact .binop (ihLhs hlhs) (ihRhs hrhs)
      · simp at h
    · simp at h
  | construct data ctor args arg ihArg =>
    simp only [typeOfAux] at h
    split at h
    · rename_i hargs
      split at h
      · rename_i payload argType hconstructor harg
        split at h
        · rename_i payloadEq
          have payloadEq' : payload = argType :=
            (Ty.beq_iff_eq payload argType).mp payloadEq
          subst argType
          simp at h
          subst type
          exact .construct hconstructor hargs (ihArg harg)
        · simp at h
      · simp at h
    · simp at h
  | case scrutinee pattern onMatch onFail ihScrutinee ihMatch ihFail =>
    simp only [typeOfAux] at h
    split at h
    · rename_i scrutineeType hscrutinee
      split at h
      · rename_i bindings hpattern
        split at h
        · rename_i hcontext
          split at h
          · rename_i matchType failType hmatch hfail
            split at h
            · rename_i typesEq
              have typesEq' : matchType = failType :=
                (Ty.beq_iff_eq matchType failType).mp typesEq
              subst failType
              simp at h
              subst type
              exact .case (ihScrutinee hscrutinee) hpattern hcontext
                (ihMatch hmatch) (ihFail hfail)
            · simp at h
          · simp at h
        · simp at h
      · simp at h
    · simp at h
  | fail type =>
    simp only [typeOfAux] at h
    split at h
    · rename_i htype
      simp at h
      subst type
      exact .fail htype
    · simp at h
  | raise type message ihMessage =>
    simp only [typeOfAux] at h
    split at h
    · rename_i htype
      split at h
      · rename_i hmessage
        simp at h
        subst type
        exact .raise htype (ihMessage hmessage)
      · simp at h
    · simp at h

theorem typeOfAux_complete {sig : Signature} {depth : Nat} {env : TyEnv}
    {expr : Expr} {type : Ty}
    (h : HasType sig depth env expr type) :
    typeOfAux sig depth env expr = some type := by
  induction h with
  | var hindex hinstantiate hargs =>
    simp [typeOfAux, typesScoped, hargs, TyEnv.instantiate, hindex, hinstantiate]
  | int | bool | float | string | unit => rfl
  | lam hdomain _body hbody => simp [typeOfAux, hdomain, hbody]
  | fix hdomain hcodomain _body hbody => simp [typeOfAux, hdomain, hcodomain, hbody]
  | app _ _ ihFn ihArg => simp [typeOfAux, ihFn, ihArg]
  | letE hscheme _value _body ihValue ihBody => simp [typeOfAux, hscheme, ihValue, ihBody]
  | ite _ _ _ ihCondition ihThen ihElse =>
    simp [typeOfAux, ihCondition, ihThen, ihElse]
  | pair _ _ ihFirst ihSecond => simp [typeOfAux, ihFirst, ihSecond]
  | fst _ ih => simp [typeOfAux, ih]
  | snd _ ih => simp [typeOfAux, ih]
  | binop _ _ ihLhs ihRhs => simp [typeOfAux, ihLhs, ihRhs]
  | construct hconstructor hargs _arg ihArg =>
    simp [typeOfAux, typesScoped, hargs, hconstructor, ihArg]
  | case _ hpattern hcontext _onMatch _onFail ihScrutinee ihMatch ihFail =>
    simp [typeOfAux, ihScrutinee, hpattern, hcontext, ihMatch, ihFail]
  | fail htype => simp [typeOfAux, htype]
  | raise htype _message ihMessage => simp [typeOfAux, htype, ihMessage]

theorem typeOf_sound {sig : Signature} {depth : Nat} {env : TyEnv}
    {expr : Expr} {type : Ty}
    (h : typeOf sig depth env expr = some type) :
    HasType sig depth env expr type := by
  unfold typeOf at h
  split at h
  · exact typeOfAux_sound h
  · simp at h

theorem typeOf_complete {sig : Signature} {depth : Nat} {env : TyEnv}
    {expr : Expr} {type : Ty}
    (hsig : sig.wellFormed = true)
    (henv : env.wellScoped sig.arities depth = true)
    (h : HasType sig depth env expr type) :
    typeOf sig depth env expr = some type := by
  simp [typeOf, hsig, henv, typeOfAux_complete h]

theorem hasType_iff_typeOf {sig : Signature} {depth : Nat} {env : TyEnv}
    {expr : Expr} {type : Ty}
    (hsig : sig.wellFormed = true)
    (henv : env.wellScoped sig.arities depth = true) :
    HasType sig depth env expr type ↔ typeOf sig depth env expr = some type :=
  ⟨typeOf_complete hsig henv, typeOf_sound⟩

end Hypomnesis.Core.Poly
