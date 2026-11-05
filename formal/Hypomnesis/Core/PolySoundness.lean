import Hypomnesis.Core.Soundness
import Hypomnesis.Core.PolyTyping
import Hypomnesis.Core.PolySyntaxExamples

/-! # Pont de sûreté polymorphe pour des fragments runtime contrôlés -/

namespace Hypomnesis.Core.Poly

/-- Effacement spécialisé pour le fragment runtime : contrairement à
`Expr.erase`, il conserve les annotations monomorphes des fonctions. -/
def Expr.eraseMono : Expr → Core.Expr
  | .var index _ => .var index
  | .int value => .int value
  | .bool value => .bool value
  | .float value => .float value
  | .string value => .string value
  | .unit => .unit
  | .lam domain body => .lam domain.erase body.eraseMono
  | .fix domain codomain body =>
    .fix domain.erase codomain.erase body.eraseMono
  | .app fn arg => .app fn.eraseMono arg.eraseMono
  | .letE _ value body => .letE value.eraseMono body.eraseMono
  | .ite condition thenBranch elseBranch =>
    .ite condition.eraseMono thenBranch.eraseMono elseBranch.eraseMono
  | .pair first second => .pair first.eraseMono second.eraseMono
  | .fst expr => .fst expr.eraseMono
  | .snd expr => .snd expr.eraseMono
  | .binop op lhs rhs => .binop op lhs.eraseMono rhs.eraseMono
  | .construct data ctor _ arg => .construct data ctor arg.eraseMono
  | .case scrutinee pattern onMatch onFail =>
    .case scrutinee.eraseMono pattern onMatch.eraseMono onFail.eraseMono
  | .fail _ => .fail .unit
  | .raise _ message => .raise .unit message.eraseMono

/-- Motifs non nominaux, partageant directement la sémantique de filtrage Core. -/
inductive RuntimePat : Pat → Prop where
  | wild : RuntimePat .wild
  | var : RuntimePat .var
  | int (value : Int) : RuntimePat (.int value)
  | bool (value : Bool) : RuntimePat (.bool value)
  | float (value : Float) : RuntimePat (.float value)
  | string (value : String) : RuntimePat (.string value)
  | pair {first second} : RuntimePat first → RuntimePat second →
      RuntimePat (.pair first second)

def Signature.eraseMono (sig : Signature) : Core.Sig :=
  sig.map fun declaration => declaration.constructors.map Ty.erase

theorem Signature.eraseMono_declLookup {sig : Signature} {data : Nat}
    {declaration : DataDecl} (lookup : sig[data]? = some declaration) :
    sig.eraseMono[data]? = some (declaration.constructors.map Ty.erase) := by
  simp [Signature.eraseMono, lookup]

theorem Signature.eraseMono_constructorLookup {sig : Signature} {data ctor : Nat}
    {declaration : DataDecl} {payload : Ty}
    (declLookup : sig[data]? = some declaration)
    (ctorLookup : declaration.constructors[ctor]? = some payload) :
    ∃ constructors,
      sig.eraseMono[data]? = some constructors ∧
      constructors[ctor]? = some payload.erase := by
  refine ⟨declaration.constructors.map Ty.erase, ?_, ?_⟩
  · exact Signature.eraseMono_declLookup declLookup
  · simpa using congrArg (Option.map Ty.erase) ctorLookup

theorem Signature.constructorType_zeroArity {sig : Signature} {data ctor : Nat}
    {declaration : DataDecl} {payload : Ty}
    (declLookup : sig[data]? = some declaration) (arity : declaration.parameters = 0)
    (ctorLookup : declaration.constructors[ctor]? = some payload) :
    sig.constructorType data ctor [] = some payload := by
  simp [Signature.constructorType, declLookup, ctorLookup,
    Scheme.instantiate, arity]
  have instantiateEmpty : instantiateSubst [] = Ty.var := by
    funext index
    simp [instantiateSubst]
  rw [instantiateEmpty, Ty.subst_var]

theorem HasType.erase_monoConstructor {sig : Signature} {data ctor : Nat}
    {declaration : DataDecl} {payload : Ty} {arg : Core.Expr}
    (declLookup : sig[data]? = some declaration)
    (ctorLookup : declaration.constructors[ctor]? = some payload)
    (argTyped : Core.HasType sig.eraseMono [] arg payload.erase) :
    Core.HasType sig.eraseMono [] (.construct data ctor arg) (.data data) := by
  obtain ⟨constructors, dataLookup, payloadLookup⟩ :=
    Signature.eraseMono_constructorLookup declLookup ctorLookup
  exact Core.HasType.construct dataLookup payloadLookup argTyped

def monoBoxDeclaration : DataDecl :=
  { parameters := 0, constructors := [.int] }

def monoBoxSignature : Signature := [monoBoxDeclaration]

def monoBoxValue : Expr :=
  .construct 0 0 [] (.int 5)

theorem monoBoxValue_has_poly_type :
    HasType monoBoxSignature 0 [] monoBoxValue (.data 0 []) := by
  have constructorType :
      monoBoxSignature.constructorType 0 0 [] = some .int := by
    apply Signature.constructorType_zeroArity (declaration := monoBoxDeclaration)
    · rfl
    · rfl
    · rfl
  exact .construct constructorType (by simp) .int

theorem monoBoxValue_erases_to_core_typed :
    Core.HasType monoBoxSignature.eraseMono [] monoBoxValue.erase (.data 0) := by
  exact HasType.erase_monoConstructor (declaration := monoBoxDeclaration)
    (by rfl) (by rfl) Core.HasType.int

theorem eval_monoBoxValue :
    Core.eval 10 [] monoBoxValue.erase = .ok (.con 0 (.int 5)) := by
  rfl

theorem eval_safe_monoBoxValue (fuel : Nat) :
    Core.Safe monoBoxSignature.eraseMono
      (Core.eval fuel [] monoBoxValue.erase) (.data 0) :=
  Core.eval_safe fuel Core.EnvTy.nil monoBoxValue_erases_to_core_typed

theorem monoBoxValue_type_and_runtime_safe (fuel : Nat) :
    HasType monoBoxSignature 0 [] monoBoxValue (.data 0 []) ∧
    Core.Safe monoBoxSignature.eraseMono
      (Core.eval fuel [] monoBoxValue.erase) (.data 0) :=
  ⟨monoBoxValue_has_poly_type, eval_safe_monoBoxValue fuel⟩

def monoBoxPatternCase : Expr :=
  .case monoBoxValue (.ctor 0 .var) (.var 0 []) (.int 0)

theorem PatTy.erase_runtimePat {sig : Signature} {coreSig : Core.Sig}
    {pattern : Pat} {type : Ty} {bindings : List Ty} (runtimePat : RuntimePat pattern)
    (typed : PatTy sig pattern type = some bindings) :
    Core.PatTy coreSig pattern type.erase (bindings.map Ty.erase) := by
  induction runtimePat generalizing type bindings with
  | wild =>
    simp only [PatTy] at typed
    cases typed
    exact Core.PatTy.wild
  | var =>
    simp only [PatTy] at typed
    cases typed
    exact Core.PatTy.var
  | int value =>
    cases type with
    | int =>
      simp only [PatTy] at typed
      cases typed
      exact Core.PatTy.int
    | _ => simp [PatTy] at typed
  | bool value =>
    cases type with
    | bool =>
      simp only [PatTy] at typed
      cases typed
      exact Core.PatTy.bool
    | _ => simp [PatTy] at typed
  | float value =>
    cases type with
    | float =>
      simp only [PatTy] at typed
      cases typed
      exact Core.PatTy.float
    | _ => simp [PatTy] at typed
  | string value =>
    cases type with
    | string =>
      simp only [PatTy] at typed
      cases typed
      exact Core.PatTy.string
    | _ => simp [PatTy] at typed
  | @pair first second firstPat secondPat ihFirst ihSecond =>
    cases type with
    | prod firstType secondType =>
      simp only [PatTy] at typed
      cases hFirst : PatTy sig first firstType with
      | none => simp [hFirst] at typed
      | some firstBindings =>
        cases hSecond : PatTy sig second secondType with
        | none => simp [hFirst, hSecond] at typed
        | some secondBindings =>
          simp only [hFirst, hSecond, Option.some.injEq] at typed
          subst bindings
          simpa [List.map_append, Ty.erase] using
            Core.PatTy.pair (ihFirst hFirst) (ihSecond hSecond)
    | _ => simp [PatTy] at typed

/-- Un motif de constructeur d'une déclaration sans paramètres s'efface vers
le motif Core correspondant, lorsque son motif d'argument appartient au
fragment runtime déjà vérifié. -/
theorem PatTy.erase_monoCtorPattern {sig : Signature} {data ctor : Nat}
    {declaration : DataDecl} {payload : Ty} {pattern : Pat} {bindings : List Ty}
    (declLookup : sig[data]? = some declaration)
    (arity : declaration.parameters = 0)
    (ctorLookup : declaration.constructors[ctor]? = some payload)
    (runtimePat : RuntimePat pattern)
    (innerTyped : PatTy sig pattern payload = some bindings) :
    PatTy sig (.ctor ctor pattern) (.data data []) = some bindings ∧
      Core.PatTy sig.eraseMono (.ctor ctor pattern) (.data data)
        (bindings.map Ty.erase) := by
  have constructorType :=
    Signature.constructorType_zeroArity declLookup arity ctorLookup
  have polyPattern :
      PatTy sig (.ctor ctor pattern) (.data data []) = some bindings := by
    simp [PatTy, constructorType, innerTyped]
  obtain ⟨constructors, dataLookup, payloadLookup⟩ :=
    Signature.eraseMono_constructorLookup declLookup ctorLookup
  have corePattern : Core.PatTy sig.eraseMono (.ctor ctor pattern)
      (.data data) (bindings.map Ty.erase) :=
    Core.PatTy.ctor dataLookup payloadLookup
      (PatTy.erase_runtimePat runtimePat innerTyped)
  exact ⟨polyPattern, corePattern⟩

theorem monoBoxPatternCase_has_poly_type :
    HasType monoBoxSignature 0 [] monoBoxPatternCase .int := by
  have patternInfo :
      PatTy monoBoxSignature (.ctor 0 .var) (.data 0 []) = some [.int] ∧
        Core.PatTy monoBoxSignature.eraseMono (.ctor 0 .var) (.data 0) [.int] :=
    PatTy.erase_monoCtorPattern (data := 0) (ctor := 0)
      (declaration := monoBoxDeclaration) (payload := .int)
      (by rfl) (by rfl) (by rfl) RuntimePat.var (by rfl)
  have matchTyped :
      HasType monoBoxSignature 0 [mono .int] (.var 0 []) .int := by
    exact .var rfl (by simp [mono, Scheme.instantiate, Ty.subst]) (by simp)
  apply HasType.case (scrutineeType := .data 0 []) (bindings := [.int])
  · exact monoBoxValue_has_poly_type
  · exact patternInfo.1
  · simp [TyEnv.wellScoped, Scheme.wellScoped, Ty.wellScoped,
      Signature.arities, mono, monoBoxSignature]
  · exact matchTyped
  · exact .int

theorem eval_safe_monoBoxPatternCase (fuel : Nat) :
    Core.Safe monoBoxSignature.eraseMono
      (Core.eval fuel [] monoBoxPatternCase.erase) .int := by
  have patternInfo :
      PatTy monoBoxSignature (.ctor 0 .var) (.data 0 []) = some [.int] ∧
        Core.PatTy monoBoxSignature.eraseMono (.ctor 0 .var) (.data 0) [.int] :=
    PatTy.erase_monoCtorPattern (data := 0) (ctor := 0)
      (declaration := monoBoxDeclaration) (payload := .int)
      (by rfl) (by rfl) (by rfl) RuntimePat.var (by rfl)
  have coreTyped : Core.HasType monoBoxSignature.eraseMono [] monoBoxPatternCase.erase .int := by
    simpa [monoBoxPatternCase, Expr.erase] using
      (Core.HasType.case monoBoxValue_erases_to_core_typed patternInfo.2
        (Core.HasType.var rfl) Core.HasType.int)
  exact Core.eval_safe fuel Core.EnvTy.nil coreTyped

theorem eval_monoBoxPatternCase :
    Core.eval 20 [] monoBoxPatternCase.erase = .ok (.int 5) := by
  rfl

/-- Sous-fragment fermé par les formes de contrôle et les `let` monomorphes ;
les variables sans arguments de type, les fonctions monomorphes, les `fix`
monomorphes et les motifs non nominaux sont permis. -/
inductive RuntimeFragment : Expr → Prop where
  | var (index : Nat) : RuntimeFragment (.var index [])
  | int (value : Int) : RuntimeFragment (.int value)
  | bool (value : Bool) : RuntimeFragment (.bool value)
  | float (value : Float) : RuntimeFragment (.float value)
  | string (value : String) : RuntimeFragment (.string value)
  | unit : RuntimeFragment .unit
  | lam {domain body} :
      RuntimeFragment body → body.eraseMono = body.erase →
      RuntimeFragment (.lam domain body)
  | fix {domain codomain body} :
      RuntimeFragment body → body.eraseMono = body.erase →
      RuntimeFragment (.fix domain codomain body)
  | app {fn arg} : RuntimeFragment fn → RuntimeFragment arg → RuntimeFragment (.app fn arg)
  | ite {condition thenBranch elseBranch} :
      RuntimeFragment condition → RuntimeFragment thenBranch → RuntimeFragment elseBranch →
      RuntimeFragment (.ite condition thenBranch elseBranch)
  | pair {first second} :
      RuntimeFragment first → RuntimeFragment second → RuntimeFragment (.pair first second)
  | fst {expr} : RuntimeFragment expr → RuntimeFragment (.fst expr)
  | snd {expr} : RuntimeFragment expr → RuntimeFragment (.snd expr)
  | binop {op lhs rhs} :
      RuntimeFragment lhs → RuntimeFragment rhs → RuntimeFragment (.binop op lhs rhs)
  | letE {scheme value body} :
      scheme.arity = 0 →
      RuntimeFragment value → RuntimeFragment body →
      RuntimeFragment (.letE scheme value body)
  | case {scrutinee pattern onMatch onFail} :
      RuntimeFragment scrutinee → RuntimePat pattern →
      RuntimeFragment onMatch → RuntimeFragment onFail →
      RuntimeFragment (.case scrutinee pattern onMatch onFail)

/-- Pour les termes du fragment, l'effacement spécialisé préserve exactement
le résultat du véritable évaluateur Core. Les lambdas garantissent que leur
corps stocké dans une fermeture est identique après effacement. -/
theorem Expr.eval_eraseMono_eq_erase (fuel : Nat) (env : List Core.Val)
    {expr : Expr} (fragment : RuntimeFragment expr) :
    Core.eval fuel env expr.eraseMono = Core.eval fuel env expr.erase := by
  induction fragment generalizing fuel env with
  | var | int | bool | float | string | unit =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval]
  | lam bodyFragment bodyEraseEq =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, bodyEraseEq]
  | fix bodyFragment bodyEraseEq =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, bodyEraseEq]
  | app fnFragment argFragment ihFn ihArg =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, ihFn, ihArg]
  | ite conditionFragment thenFragment elseFragment ihCondition ihThen ihElse =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval,
      ihCondition, ihThen, ihElse]
  | pair firstFragment secondFragment ihFirst ihSecond =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, ihFirst, ihSecond]
  | fst exprFragment ih | snd exprFragment ih =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, ih]
  | binop lhsFragment rhsFragment ihLhs ihRhs =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, ihLhs, ihRhs]
  | letE _ valueFragment bodyFragment ihValue ihBody =>
    cases fuel <;> simp [Expr.eraseMono, Expr.erase, Core.eval, ihValue, ihBody]
  | case scrutineeFragment _ matchFragment failFragment ihScrutinee ihMatch ihFail =>
    cases fuel <;>
      simp [Expr.eraseMono, Expr.erase, Core.eval, ihScrutinee, ihMatch, ihFail]

/-- Le fragment de liaison de ce pont n'autorise que des schémas monomorphes. -/
def MonoTyEnv (env : TyEnv) : Prop :=
  ∀ scheme, scheme ∈ env → scheme.arity = 0

@[simp] theorem Scheme.weaken_zero (scheme : Scheme) : scheme.weaken 0 = scheme := by
  cases scheme
  simp [Scheme.weaken, Scheme.subst]

@[simp] theorem TyEnv.weaken_zero (env : TyEnv) : TyEnv.weaken 0 env = env := by
  induction env with
  | nil => rfl
  | cons scheme env ih =>
    change scheme.weaken 0 :: TyEnv.weaken 0 env = scheme :: env
    rw [Scheme.weaken_zero, ih]

/-- Relation entre un environnement polymorphe monomorphe et l'environnement
runtime Core après effacement des types. Les valeurs sont interprétées par
`Core.ValTy` au type effacé de chaque liaison. -/
inductive RuntimeEnvRel : List Core.Val → TyEnv → Prop where
  | nil : RuntimeEnvRel [] []
  | cons {value scheme values env} :
      scheme.arity = 0 →
      Core.ValTy [] value scheme.body.erase →
      RuntimeEnvRel values env →
      RuntimeEnvRel (value :: values) (scheme :: env)

/-- Interprétation relationnelle d'un type. Les variables de type sont
interprétées par des relations arbitraires sur les valeurs Core ; une
fermeture est interprétée par le comportement de son corps à chaque budget.
Les fermetures récursives et les valeurs de constructeurs sont hors fragment. -/
def PolyValueRel : Ty → (Nat → Core.Val → Prop) → Core.Val → Prop
  | .var index, relations, value => relations index value
  | .int, _, .int _ => True
  | .bool, _, .bool _ => True
  | .float, _, .float _ => True
  | .string, _, .string _ => True
  | .unit, _, .unit => True
  | .arrow domain codomain, relations, .clo env body =>
      ∀ argument, PolyValueRel domain relations argument →
        ∀ fuel,
          match Core.eval fuel (argument :: env) body with
          | .ok result => PolyValueRel codomain relations result
          | .stuck => False
          | .timeout | .matchFail | .error _ => True
  | .prod first second, relations, .pair firstValue secondValue =>
      PolyValueRel first relations firstValue ∧
        PolyValueRel second relations secondValue
  | _, _, _ => False
termination_by type _ _ => sizeOf type
decreasing_by all_goals simp_wf <;> omega

/-- Relation d'un résultat d'évaluation : seuls timeout, échec de motif et
erreur explicite sont admis sans valeur ; `stuck` reste exclu. -/
def PolyResultRel (type : Ty) (relations : Nat → Core.Val → Prop) :
    Core.Res → Prop
  | .ok value => PolyValueRel type relations value
  | .stuck => False
  | .timeout | .matchFail | .error _ => True

/-- Fragment source du pont polymorphe : variables instanciées, valeurs
primitives, fermetures non récursives, applications et paires. -/
inductive PolyRuntimeFragment : Expr → Prop where
  | var (index : Nat) (args : List Ty) : PolyRuntimeFragment (.var index args)
  | int (value : Int) : PolyRuntimeFragment (.int value)
  | bool (value : Bool) : PolyRuntimeFragment (.bool value)
  | float (value : Float) : PolyRuntimeFragment (.float value)
  | string (value : String) : PolyRuntimeFragment (.string value)
  | unit : PolyRuntimeFragment .unit
  | lam {domain body} :
      PolyRuntimeFragment body → PolyRuntimeFragment (.lam domain body)
  | app {fn arg} :
      PolyRuntimeFragment fn → PolyRuntimeFragment arg →
      PolyRuntimeFragment (.app fn arg)
  | pair {first second} :
      PolyRuntimeFragment first → PolyRuntimeFragment second →
      PolyRuntimeFragment (.pair first second)

/-- Le lien `Res.bind` conserve la relation de résultat. -/
theorem PolyResultRel.bind {input output : Ty}
    {relations : Nat → Core.Val → Prop} {result : Core.Res}
    {continuation : Core.Val → Core.Res}
    (resultRel : PolyResultRel input relations result)
    (continuationRel : ∀ value, PolyValueRel input relations value →
      PolyResultRel output relations (continuation value)) :
    PolyResultRel output relations (Core.Res.bind result continuation) := by
  cases result with
  | ok value => exact continuationRel value resultRel
  | stuck => exact False.elim resultRel
  | timeout | matchFail | error _ => trivial

/-- Substituer des types dans la syntaxe correspond à interpréter chaque
variable par la relation du type qui la remplace. -/
theorem PolyValueRel.subst (type : Ty) (substitution : Nat → Ty)
    (relations : Nat → Core.Val → Prop) (value : Core.Val) :
    PolyValueRel (type.subst substitution) relations value ↔
      PolyValueRel type
        (fun index => PolyValueRel (substitution index) relations) value := by
  induction type using Ty.induct generalizing relations value with
  | var index =>
    simp [Ty.subst, PolyValueRel]
  | int | bool | float | string | unit =>
    cases value <;> simp [Ty.subst, PolyValueRel]
  | arrow domain codomain ihDomain ihCodomain =>
    cases value with
    | clo env body =>
      simp only [Ty.subst, PolyValueRel]
      constructor
      · intro h argument argumentRel fuel
        have argumentRel' :=
          (ihDomain relations argument).mpr argumentRel
        have resultRel := h argument argumentRel' fuel
        cases hEval : Core.eval fuel (argument :: env) body with
        | ok result =>
          exact (ihCodomain relations result).mp (by simpa [hEval] using resultRel)
        | stuck => simp [hEval] at resultRel
        | timeout | matchFail | error _ => trivial
      · intro h argument argumentRel fuel
        have argumentRel' :=
          (ihDomain relations argument).mp argumentRel
        have resultRel := h argument argumentRel' fuel
        cases hEval : Core.eval fuel (argument :: env) body with
        | ok result =>
          exact (ihCodomain relations result).mpr (by simpa [hEval] using resultRel)
        | stuck => simp [hEval] at resultRel
        | timeout | matchFail | error _ => trivial
    | _ => simp [Ty.subst, PolyValueRel]
  | prod first second ihFirst ihSecond =>
    cases value with
    | pair firstValue secondValue =>
      simp only [Ty.subst, PolyValueRel]
      exact and_congr (ihFirst relations firstValue) (ihSecond relations secondValue)
    | _ => simp [Ty.subst, PolyValueRel]
  | data index args ih =>
    simp [Ty.subst, PolyValueRel]

/-- Relation d'une valeur Core avec un schéma : les relations liées par le
schéma sont universelles, tandis que les variables extérieures gardent leur
interprétation. -/
def PolySchemeRel (scheme : Scheme) (outer : Nat → Core.Val → Prop)
    (value : Core.Val) : Prop :=
  ∀ (bound : Nat → Core.Val → Prop),
    PolyValueRel scheme.body
      (fun index =>
        if index < scheme.arity then bound index
        else outer (index - scheme.arity))
      value

/-- Types sans variables ni constructeurs de données, pour lesquels la
relation des valeurs implique le typage Core ordinaire. -/
inductive FirstOrderRuntimeTy : Ty → Prop where
  | int : FirstOrderRuntimeTy .int
  | bool : FirstOrderRuntimeTy .bool
  | float : FirstOrderRuntimeTy .float
  | string : FirstOrderRuntimeTy .string
  | unit : FirstOrderRuntimeTy .unit
  | prod {first second} :
      FirstOrderRuntimeTy first → FirstOrderRuntimeTy second →
      FirstOrderRuntimeTy (.prod first second)

theorem PolyValueRel.toCoreValTy {type : Ty}
    (firstOrder : FirstOrderRuntimeTy type) (relations : Nat → Core.Val → Prop)
    {value : Core.Val} (related : PolyValueRel type relations value) :
    Core.ValTy [] value type.erase := by
  induction firstOrder generalizing relations value with
  | int =>
    cases value with
    | int n => exact Core.ValTy.int
    | _ => simp [PolyValueRel] at related
  | bool =>
    cases value with
    | bool b => exact Core.ValTy.bool
    | _ => simp [PolyValueRel] at related
  | float =>
    cases value with
    | float f => exact Core.ValTy.float
    | _ => simp [PolyValueRel] at related
  | string =>
    cases value with
    | string s => exact Core.ValTy.string
    | _ => simp [PolyValueRel] at related
  | unit =>
    cases value with
    | unit => exact Core.ValTy.unit
    | _ => simp [PolyValueRel] at related
  | prod firstOrderFirst firstOrderSecond ihFirst ihSecond =>
    cases value with
    | pair firstValue secondValue =>
      simp only [PolyValueRel] at related
      exact Core.ValTy.pair
        (ihFirst relations related.1)
        (ihSecond relations related.2)
    | _ => simp [PolyValueRel] at related

/-- La relation des résultats induit `Core.Safe` pour les types de sortie
d'ordre zéro. -/
theorem PolyResultRel.toCoreSafe {type : Ty}
    (firstOrder : FirstOrderRuntimeTy type)
    (relations : Nat → Core.Val → Prop) {result : Core.Res}
    (related : PolyResultRel type relations result) :
    Core.Safe [] result type.erase := by
  cases result with
  | ok value =>
    simpa [PolyResultRel, Core.Safe] using
      PolyValueRel.toCoreValTy firstOrder relations related
  | stuck => exact False.elim related
  | timeout | matchFail | error _ => trivial

/-- Environnement d'exécution associé à un environnement de schémas de rang 1. -/
inductive PolyRuntimeEnvRel (outer : Nat → Core.Val → Prop) :
    List Core.Val → TyEnv → Prop where
  | nil : PolyRuntimeEnvRel outer [] []
  | cons {value scheme values env} :
      PolySchemeRel scheme outer value →
      PolyRuntimeEnvRel outer values env →
      PolyRuntimeEnvRel outer (value :: values) (scheme :: env)

/-- Une relation de schéma fournit la relation de toute instanciation valide. -/
theorem PolySchemeRel.instantiate {scheme : Scheme} {outer : Nat → Core.Val → Prop}
    {value : Core.Val} {args : List Ty}
    (related : PolySchemeRel scheme outer value)
    (arity : args.length = scheme.arity) :
    PolyValueRel (scheme.body.subst (instantiateSubst args)) outer value := by
  let bound : Nat → Core.Val → Prop :=
    fun index value => PolyValueRel (instantiateSubst args index) outer value
  have relatedBound := related bound
  have relationEnv :
      (fun index =>
        if index < scheme.arity then bound index
        else outer (index - scheme.arity)) =
      (fun index => PolyValueRel (instantiateSubst args index) outer) := by
    funext index
    funext runtimeValue
    by_cases inRange : index < scheme.arity
    · simp [bound, instantiateSubst, inRange, arity]
    · simp [bound, instantiateSubst, arity, inRange, PolyValueRel]
  rw [PolyValueRel.subst]
  rw [← relationEnv]
  exact relatedBound

/-- Une liaison déclarée dans un environnement relié possède une valeur Core
dont la relation de schéma est préservée. -/
theorem PolyRuntimeEnvRel.lookup_exists {outer : Nat → Core.Val → Prop}
    {values : List Core.Val} {env : TyEnv}
    (related : PolyRuntimeEnvRel outer values env) :
    ∀ {index : Nat} {scheme : Scheme},
      env[index]? = some scheme →
      ∃ value, values[index]? = some value ∧ PolySchemeRel scheme outer value := by
  induction related with
  | nil =>
    intro index scheme envLookup
    simp at envLookup
  | @cons value scheme values env schemeRel _ ih =>
    intro index candidate envLookup
    cases index with
    | zero =>
      simp only [List.getElem?_cons_zero] at envLookup
      cases envLookup
      exact ⟨value, rfl, schemeRel⟩
    | succ index =>
      exact ih envLookup

/-- Théorème fondamental opérationnel pour le fragment polymorphe de base.
Une dérivation et un environnement relationnel donnent un résultat Core
relationnel à tout fuel, en distinguant `stuck` des autres issues. -/
theorem HasType.eval_polyRuntimeFragment {sig : Signature} {depth : Nat}
    {env : TyEnv} {values : List Core.Val} {expr : Expr} {type : Ty}
    {relations : Nat → Core.Val → Prop}
    (typed : HasType sig depth env expr type)
    (fragment : PolyRuntimeFragment expr)
    (envRel : PolyRuntimeEnvRel relations values env) :
    ∀ fuel, PolyResultRel type relations
      (Core.eval fuel values expr.erase) := by
  induction typed generalizing values relations with
  | var envLookup instantiated argsScoped =>
    rename_i env' depth' index args scheme resultType
    cases fragment with
    | var _ _ =>
      have arity : args.length = scheme.arity := by
        by_cases lengthEq : args.length = scheme.arity
        · exact lengthEq
        · simp [Scheme.instantiate, lengthEq] at instantiated
      have typeEq : resultType = scheme.body.subst (instantiateSubst args) := by
        have h := instantiated
        simp [Scheme.instantiate, arity] at h
        exact h.symm
      obtain ⟨value, valueLookup, schemeRel⟩ :=
        envRel.lookup_exists envLookup
      have valueRel := PolySchemeRel.instantiate schemeRel arity
      intro fuel
      cases fuel with
      | zero => simp [Core.eval, PolyResultRel]
      | succ fuel =>
        simp [Core.eval, Expr.erase, valueLookup, PolyResultRel, typeEq, valueRel]
  | int =>
    cases fragment with
    | int _ =>
      intro fuel
      cases fuel <;> simp [Core.eval, Expr.erase, PolyResultRel, PolyValueRel]
  | bool =>
    cases fragment with
    | bool _ =>
      intro fuel
      cases fuel <;> simp [Core.eval, Expr.erase, PolyResultRel, PolyValueRel]
  | float =>
    cases fragment with
    | float _ =>
      intro fuel
      cases fuel <;> simp [Core.eval, Expr.erase, PolyResultRel, PolyValueRel]
  | string =>
    cases fragment with
    | string _ =>
      intro fuel
      cases fuel <;> simp [Core.eval, Expr.erase, PolyResultRel, PolyValueRel]
  | unit =>
    cases fragment with
    | unit =>
      intro fuel
      cases fuel <;> simp [Core.eval, Expr.erase, PolyResultRel, PolyValueRel]
  | lam domainScoped bodyTyped ih =>
    rename_i domain body codomain
    cases fragment with
    | lam bodyFragment =>
      intro fuel
      cases fuel with
      | zero => simp [Core.eval, PolyResultRel]
      | succ fuel =>
        simp only [Core.eval, Expr.erase, PolyResultRel]
        simp only [PolyValueRel]
        intro argument argumentRel bodyFuel
        have argumentSchemeRel : PolySchemeRel (mono domain) relations argument := by
          intro bound
          simpa [PolySchemeRel, mono] using argumentRel
        exact ih bodyFragment
          (PolyRuntimeEnvRel.cons argumentSchemeRel envRel) bodyFuel
  | app fnTyped argTyped ihFn ihArg =>
    rename_i fn arg domain codomain
    cases fragment with
    | app fnFragment argFragment =>
      intro fuel
      cases fuel with
      | zero => simp [Core.eval, PolyResultRel]
      | succ fuel =>
        change PolyResultRel codomain relations
          ((Core.eval fuel values fn.erase).bind fun fnValue =>
            (Core.eval fuel values arg.erase).bind fun argValue =>
              match fnValue with
              | .clo closureEnv body => Core.eval fuel (argValue :: closureEnv) body
              | .rclo closureEnv body =>
                  Core.eval fuel (argValue :: fnValue :: closureEnv) body
              | _ => .stuck)
        apply PolyResultRel.bind (ihFn fnFragment envRel fuel)
        intro fnValue fnValueRel
        apply PolyResultRel.bind (ihArg argFragment envRel fuel)
        intro argValue argValueRel
        have fnPolyRel : PolyValueRel (.arrow domain codomain) relations fnValue :=
          fnValueRel
        cases fnValue with
        | clo closureEnv body =>
          have closureApplyRel :
              ∀ argument, PolyValueRel domain relations argument → ∀ fuel,
                match Core.eval fuel (argument :: closureEnv) body with
                | .ok result => PolyValueRel codomain relations result
                | .stuck => False
                | .timeout | .matchFail | .error _ => True := by
            simpa only [PolyValueRel] using fnPolyRel
          simpa only [PolyResultRel] using
            closureApplyRel argValue argValueRel fuel
        | rclo _ _ => simp [PolyValueRel] at fnPolyRel
        | int _ => simp [PolyValueRel] at fnPolyRel
        | bool _ => simp [PolyValueRel] at fnPolyRel
        | float _ => simp [PolyValueRel] at fnPolyRel
        | string _ => simp [PolyValueRel] at fnPolyRel
        | unit => simp [PolyValueRel] at fnPolyRel
        | pair _ _ => simp [PolyValueRel] at fnPolyRel
        | con _ _ => simp [PolyValueRel] at fnPolyRel
  | pair firstTyped secondTyped ihFirst ihSecond =>
    rename_i first second firstType secondType
    cases fragment with
    | pair firstFragment secondFragment =>
      intro fuel
      cases fuel with
      | zero => simp [Core.eval, PolyResultRel]
      | succ fuel =>
        change PolyResultRel (.prod firstType secondType) relations
          ((Core.eval fuel values first.erase).bind fun firstValue =>
            (Core.eval fuel values second.erase).bind fun secondValue =>
              .ok (.pair firstValue secondValue))
        apply PolyResultRel.bind (ihFirst firstFragment envRel fuel)
        intro firstValue firstRel
        apply PolyResultRel.bind (ihSecond secondFragment envRel fuel)
        intro secondValue secondRel
        simp [PolyResultRel, PolyValueRel, firstRel, secondRel]
  | fix => cases fragment
  | letE => cases fragment
  | ite => cases fragment
  | fst => cases fragment
  | snd => cases fragment
  | binop => cases fragment
  | construct => cases fragment
  | case => cases fragment
  | fail => cases fragment
  | raise => cases fragment

/-- Une fermeture relationnelle appliquée à une valeur liée ne se bloque
jamais ; tout résultat produit conserve la relation de sortie. -/
theorem PolyValueRel.closure_application_safe
    {domain codomain : Ty} {relations : Nat → Core.Val → Prop}
    {env : List Core.Val} {body : Core.Expr} {argument : Core.Val}
    (closureRel : PolyValueRel (.arrow domain codomain) relations (.clo env body))
    (argumentRel : PolyValueRel domain relations argument) (fuel : Nat) :
    Core.eval fuel (argument :: env) body ≠ .stuck ∧
      ∀ result, Core.eval fuel (argument :: env) body = .ok result →
        PolyValueRel codomain relations result := by
  have applyRel : ∀ argument, PolyValueRel domain relations argument → ∀ fuel,
      match Core.eval fuel (argument :: env) body with
      | .ok result => PolyValueRel codomain relations result
      | .stuck => False
      | .timeout | .matchFail | .error _ => True := by
    simpa only [PolyValueRel] using closureRel
  have related := applyRel argument argumentRel fuel
  cases hEval : Core.eval fuel (argument :: env) body with
  | ok result =>
    simp only [hEval] at related
    exact ⟨by simp, fun value valueEq => by
      cases valueEq
      exact related⟩
  | stuck =>
    simp [hEval] at related
  | timeout | matchFail | error _ =>
    exact ⟨by simp, by intro result resultEq; simp at resultEq⟩

/-- Le résultat relationnel d'une fermeture polymorphe dans un type d'ordre
zéro fournit la sûreté du véritable évaluateur Core à tout fuel. -/
theorem PolyValueRel.closure_application_coreSafe
    {domain codomain : Ty} {relations : Nat → Core.Val → Prop}
    {env : List Core.Val} {body : Core.Expr} {argument : Core.Val}
    (codomainFirstOrder : FirstOrderRuntimeTy codomain)
    (closureRel : PolyValueRel (.arrow domain codomain) relations (.clo env body))
    (argumentRel : PolyValueRel domain relations argument) (fuel : Nat) :
    Core.Safe [] (Core.eval fuel (argument :: env) body) codomain.erase := by
  have application := PolyValueRel.closure_application_safe
    closureRel argumentRel fuel
  cases hEval : Core.eval fuel (argument :: env) body with
  | ok result =>
    have resultRel : PolyValueRel codomain relations result := by
      exact (application.2 result hEval)
    simpa [Core.Safe] using
      PolyValueRel.toCoreValTy codomainFirstOrder relations resultRel
  | stuck => exact False.elim (application.1 hEval)
  | timeout | matchFail | error _ => trivial

/-- Toute lecture d'un environnement relié conserve la relation de son schéma
après instanciation des variables quantifiées. -/
theorem PolyRuntimeEnvRel.lookup {outer : Nat → Core.Val → Prop}
    {values : List Core.Val} {env : TyEnv}
    (related : PolyRuntimeEnvRel outer values env) :
    ∀ {index : Nat} {scheme : Scheme} {value : Core.Val} {args : List Ty},
      env[index]? = some scheme → values[index]? = some value →
      args.length = scheme.arity →
      PolyValueRel (scheme.body.subst (instantiateSubst args)) outer value := by
  induction related with
  | nil =>
    intro index scheme value args envLookup _ _
    simp at envLookup
  | @cons value scheme values env schemeRel _ ih =>
    intro index candidate runtimeValue args envLookup valueLookup arity
    cases index with
    | zero =>
      simp only [List.getElem?_cons_zero] at envLookup valueLookup
      cases envLookup
      cases valueLookup
      exact PolySchemeRel.instantiate schemeRel arity
    | succ index =>
      exact ih envLookup valueLookup arity

/-- Schéma du let identité utilisé par les régressions polymorphes. -/
def identityPolyScheme : Scheme :=
  ⟨1, .arrow (.var 0) (.var 0)⟩

/-- Valeur source du let identité dans le contexte de sa variable de type. -/
def identityPolyValueExpr : Expr :=
  .lam (.var 0) (.var 0 [])

def identityPolyBody : Expr :=
  .pair
    (.app (.var 0 [.int]) (.int 7))
    (.app (.var 0 [.bool]) (.bool true))

def identityPolyProgram : Expr :=
  .letE identityPolyScheme identityPolyValueExpr identityPolyBody

theorem identityPolyValueExpr_has_scheme_body :
    HasType [] 1 [] identityPolyValueExpr identityPolyScheme.body := by
  apply HasType.lam
  · simp [Ty.wellScoped]
  · change HasType [] 1 [mono (.var 0)] (.var 0 []) (.var 0)
    apply HasType.var
    · rfl
    · simp [mono, Scheme.instantiate, instantiateSubst, Ty.subst]
    · rfl

theorem identityPolyBody_has_type :
    HasType [] 0 [identityPolyScheme] identityPolyBody (.prod .int .bool) := by
  apply HasType.pair
  · apply HasType.app
    · show HasType [] 0 [identityPolyScheme] (.var 0 [.int])
        (.arrow .int .int)
      exact .var (by rfl)
        (by simp [identityPolyScheme, Scheme.instantiate, instantiateSubst, Ty.subst])
        (by simp [Ty.wellScoped])
    · exact .int
  · apply HasType.app
    · show HasType [] 0 [identityPolyScheme] (.var 0 [.bool])
        (.arrow .bool .bool)
      exact .var (by rfl)
        (by simp [identityPolyScheme, Scheme.instantiate, instantiateSubst, Ty.subst])
        (by simp [Ty.wellScoped])
    · exact .bool

theorem identityPolyProgram_has_type :
    HasType [] 0 [] identityPolyProgram (.prod .int .bool) := by
  apply HasType.letE (scheme := identityPolyScheme)
  · simp [identityPolyScheme, Scheme.wellScoped, Ty.wellScoped]
  · simpa [identityPolyValueExpr, identityPolyScheme, TyEnv.weaken] using
      identityPolyValueExpr_has_scheme_body
  · simpa [identityPolyBody, identityPolyScheme] using identityPolyBody_has_type

theorem identityPolyProgram_eq_syntaxExample :
    identityPolyProgram = SyntaxExamples.identityAtIntAndBool := rfl

/-- L'effacement polymorphe produit bien la fermeture runtime représentée par
la relation ; l'annotation `unit` n'est pas utilisée comme preuve de type. -/
theorem identityPolyValueExpr_evaluates_to_closure (fuel : Nat) :
    Core.eval (fuel + 1) [] identityPolyValueExpr.erase =
      .ok (.clo [] (.var 0)) := by
  rfl

/-- L'identité effacée est une fermeture relationnelle identité à tout type,
pour toute interprétation des variables de type. -/
theorem identity_closure_polyValueRel (type : Ty)
    (relations : Nat → Core.Val → Prop) :
    PolyValueRel (.arrow type type) relations (.clo [] (.var 0)) := by
  simp only [PolyValueRel]
  intro argument argumentRel fuel
  cases fuel <;> simp [Core.eval, argumentRel]

/-- Une même fermeture identité satisfait le schéma `forall a. a -> a`.
La preuve quantifie sur toutes les relations possibles de `a`, et non sur
deux types choisis à l'avance. -/
theorem identity_closure_polySchemeRel
    (outer : Nat → Core.Val → Prop) :
    PolySchemeRel identityPolyScheme outer
      (.clo [] (.var 0)) := by
  intro bound
  exact identity_closure_polyValueRel (.var 0)
    (fun index =>
      if index < 1 then bound index
      else outer (index - 1))

/-- Le résultat du véritable évaluateur après effacement de la valeur source
est bien relié au schéma polymorphe déclaré. -/
theorem identityPolyValueExpr_evaluates_to_polySchemeRel
    (outer : Nat → Core.Val → Prop) :
    ∃ value, Core.eval 1 [] identityPolyValueExpr.erase = .ok value ∧
      PolySchemeRel identityPolyScheme outer value := by
  exact ⟨.clo [] (.var 0), rfl, identity_closure_polySchemeRel outer⟩

/-- Une fermeture liée par un schéma identité reste une identité à chaque
instanciation, y compris aux types primitifs distincts. -/
theorem identity_polySchemeRel_int_bool_instances
    (outer : Nat → Core.Val → Prop) :
    PolyValueRel (.arrow .int .int) outer (.clo [] (.var 0)) ∧
      PolyValueRel (.arrow .bool .bool) outer (.clo [] (.var 0)) := by
  have related := identity_closure_polySchemeRel outer
  constructor
  · have instanceRel :=
      PolySchemeRel.instantiate (scheme := identityPolyScheme) (args := [.int])
        related (by simp [identityPolyScheme])
    simpa [identityPolyScheme, instantiateSubst, Ty.subst] using instanceRel
  · have instanceRel :=
      PolySchemeRel.instantiate (scheme := identityPolyScheme) (args := [.bool])
        related (by simp [identityPolyScheme])
    simpa [identityPolyScheme, instantiateSubst, Ty.subst] using instanceRel

/-- Le même objet runtime est lié au schéma partagé, sans spécialiser sa
fermeture dans l'environnement. -/
theorem identity_polyRuntimeEnvRel (outer : Nat → Core.Val → Prop) :
  PolyRuntimeEnvRel outer
    [.clo [] (.var 0)] [identityPolyScheme] :=
  .cons (identity_closure_polySchemeRel outer) .nil

/-- La sûreté du corps polymorphe partagé découle maintenant du théorème
fondamental sur le fragment source, et non d'une preuve par exemple. -/
theorem identity_polyBody_is_safe_at_any_fuel
    (outer : Nat → Core.Val → Prop) (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [.clo [] (.var 0)] identityPolyBody.erase)
      (.prod .int .bool) := by
  have fragment : PolyRuntimeFragment identityPolyBody := by
    exact .pair
      (.app (.var 0 [.int]) (.int 7))
      (.app (.var 0 [.bool]) (.bool true))
  have resultRel := HasType.eval_polyRuntimeFragment
    identityPolyBody_has_type fragment (identity_polyRuntimeEnvRel outer) fuel
  exact PolyResultRel.toCoreSafe (.prod .int .bool) outer resultRel

/-- Le `let` source identité partagé entre `int` et `bool` est sûr à tout
fuel par le pont relationnel ; les budgets insuffisants restent des timeouts. -/
theorem identity_polyProgram_is_safe_at_any_fuel
    (outer : Nat → Core.Val → Prop) (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] identityPolyProgram.erase)
    (.prod .int .bool) := by
  cases fuel with
  | zero => simp [Core.eval, Core.Safe]
  | succ fuel =>
    cases fuel with
    | zero =>
    simp [Core.eval, Expr.erase, Core.Res.bind, Core.Safe, identityPolyProgram]
    | succ fuel =>
    change Core.Safe [] ((Core.eval (fuel + 1) [] identityPolyValueExpr.erase).bind
      fun value => Core.eval (fuel + 1) [value] identityPolyBody.erase)
      (.prod .int .bool)
    rw [identityPolyValueExpr_evaluates_to_closure fuel]
    simp only [Core.Res.bind]
    exact identity_polyBody_is_safe_at_any_fuel outer (fuel + 1)

/-- Application d'une fermeture identité liée par le schéma polymorphe à un
entier : sûreté du `Core.eval` réel, y compris au budget épuisé. -/
theorem identity_polyClosure_int_application_safe
  (outer : Nat → Core.Val → Prop) (value : Int) (fuel : Nat) :
  Core.Safe [] (Core.eval (fuel + 1) [.clo [] (.var 0)]
    (.app (.var 0) (.int value))) .int := by
  cases fuel with
  | zero => simp [Core.eval, Core.Res.bind, Core.Safe]
  | succ fuel =>
  have closureRel := (identity_polySchemeRel_int_bool_instances outer).1
  have argumentRel : PolyValueRel .int outer (.int value) := by
    simp [PolyValueRel]
  have evalEq :
      Core.eval (fuel + 2) [.clo [] (.var 0)]
        (.app (.var 0) (.int value)) =
      Core.eval (fuel + 1) [.int value] (.var 0) := by
    simp [Core.eval, Core.Res.bind]
  rw [evalEq]
  exact PolyValueRel.closure_application_coreSafe .int closureRel argumentRel
    (fuel + 1)

/-- Même régression d'application pour une instanciation booléenne de la
même fermeture polymorphe. -/
theorem identity_polyClosure_bool_application_safe
  (outer : Nat → Core.Val → Prop) (value : Bool) (fuel : Nat) :
  Core.Safe [] (Core.eval (fuel + 1) [.clo [] (.var 0)]
    (.app (.var 0) (.bool value))) .bool := by
  cases fuel with
  | zero => simp [Core.eval, Core.Res.bind, Core.Safe]
  | succ fuel =>
  have closureRel := (identity_polySchemeRel_int_bool_instances outer).2
  have argumentRel : PolyValueRel .bool outer (.bool value) := by
    simp [PolyValueRel]
  have evalEq :
      Core.eval (fuel + 2) [.clo [] (.var 0)]
        (.app (.var 0) (.bool value)) =
      Core.eval (fuel + 1) [.bool value] (.var 0) := by
    simp [Core.eval, Core.Res.bind]
  rw [evalEq]
  exact PolyValueRel.closure_application_coreSafe .bool closureRel argumentRel
    (fuel + 1)

theorem RuntimeEnvRel.coreEnvTy {values : List Core.Val} {env : TyEnv}
  (related : RuntimeEnvRel values env) :
    Core.EnvTy [] values (env.map fun scheme => scheme.body.erase) := by
  induction related with
  | nil => exact Core.EnvTy.nil
  | cons _ valueRel _ ih =>
    simpa using Core.EnvTy.cons valueRel ih

theorem RuntimeEnvRel.monoTyEnv {values : List Core.Val} {env : TyEnv}
    (related : RuntimeEnvRel values env) : MonoTyEnv env := by
  induction related with
  | nil => intro scheme member; simp at member
  | cons hArity _ _ ih =>
    intro scheme member
    simp only [List.mem_cons] at member
    rcases member with rfl | member
    · exact hArity
    · exact ih scheme member

theorem HasType.erase_runtimeFragment {sig : Signature} {depth : Nat}
    {env : TyEnv} {expr : Expr} {type : Ty}
    (typed : HasType sig depth env expr type)
    (fragment : RuntimeFragment expr) (monoEnv : MonoTyEnv env) :
    Core.HasType [] (env.map fun scheme => scheme.body.erase) expr.eraseMono type.erase := by
  induction typed with
  | var envLookup instantiated _ =>
    rename_i env' depth' index args scheme type argsScoped
    cases fragment with
    | var index =>
      have schemeMono : scheme.arity = 0 :=
        monoEnv scheme (List.mem_of_getElem? envLookup)
      have typeEq : type = scheme.body := by
        cases scheme with
        | mk arity body =>
          have arityZero : arity = 0 := by simpa using schemeMono
          subst arity
          simp only [Scheme.instantiate, List.length_nil] at instantiated
          have instId : instantiateSubst [] = Ty.var := by
            funext i
            simp [instantiateSubst]
          rw [instId, Ty.subst_var] at instantiated
          cases instantiated
          rfl
      apply Core.HasType.var
      simp [List.getElem?_map, envLookup, typeEq]
  | int => exact Core.HasType.int
  | bool => exact Core.HasType.bool
  | float => exact Core.HasType.float
  | string => exact Core.HasType.string
  | unit => exact Core.HasType.unit
  | lam hdomain _body ihBody =>
    rename_i depth' env' domain body codomain
    cases fragment with
    | lam bodyFragment _ =>
      have monoBody : MonoTyEnv (mono domain :: env') := by
        intro scheme member
        simp only [List.mem_cons] at member
        rcases member with rfl | member
        · rfl
        · exact monoEnv scheme member
      have bodyTyped := ihBody bodyFragment monoBody
      simpa [Expr.eraseMono, mono, Ty.erase] using Core.HasType.lam bodyTyped
  | fix hdomain hcodomain _body ihBody =>
    rename_i depth' env' domain codomain body
    cases fragment with
    | fix bodyFragment _ =>
      have monoBody :
          MonoTyEnv (mono domain :: mono (.arrow domain codomain) :: env') := by
        intro scheme member
        simp only [List.mem_cons] at member
        rcases member with rfl | rfl | member
        · rfl
        · rfl
        · exact monoEnv scheme member
      have bodyTyped := ihBody bodyFragment monoBody
      simpa [Expr.eraseMono, mono, Ty.erase] using Core.HasType.fix bodyTyped
  | app _ _ ihFn ihArg =>
    cases fragment with
    | app fnFragment argFragment =>
      exact Core.HasType.app (ihFn fnFragment monoEnv) (ihArg argFragment monoEnv)
  | ite _ _ _ ihCondition ihThen ihElse =>
    cases fragment with
    | ite condition thenBranch elseBranch =>
      exact Core.HasType.ite (ihCondition condition monoEnv)
        (ihThen thenBranch monoEnv) (ihElse elseBranch monoEnv)
  | pair _ _ ihFirst ihSecond =>
    cases fragment with
    | pair first second =>
      exact Core.HasType.pair (ihFirst first monoEnv) (ihSecond second monoEnv)
  | fst _ ih =>
    cases fragment with
    | fst expr => exact Core.HasType.fst (ih expr monoEnv)
  | snd _ ih =>
    cases fragment with
    | snd expr => exact Core.HasType.snd (ih expr monoEnv)
  | binop _ _ ihLhs ihRhs =>
    cases fragment with
    | binop lhs rhs =>
      have lhsTyped := ihLhs lhs monoEnv
      have rhsTyped := ihRhs rhs monoEnv
      simp only [Ty.erase_ofCore] at lhsTyped rhsTyped
      simpa [Expr.eraseMono, Ty.erase_ofCore] using Core.HasType.binop lhsTyped rhsTyped
  | letE _ _ _ ihValue ihBody =>
    rename_i valueExpr bodyExpr resultTy schemeScoped valueDeriv bodyDeriv
    rename_i depth' env' scheme'
    cases fragment with
    | letE arity valueFragment bodyFragment =>
      have monoBody : MonoTyEnv (scheme' :: env') := by
        intro entry member
        simp only [List.mem_cons] at member
        rcases member with rfl | member
        · exact arity
        · exact monoEnv entry member
      have valueMono : MonoTyEnv (TyEnv.weaken scheme'.arity env') := by
        simpa [arity, TyEnv.weaken_zero] using monoEnv
      have valueTyped : Core.HasType [] (env'.map fun entry => entry.body.erase)
          valueExpr.eraseMono scheme'.body.erase := by
        have h := ihValue valueFragment valueMono
        simpa [arity, TyEnv.weaken_zero] using h
      have bodyTyped := ihBody bodyFragment monoBody
      simpa [Expr.eraseMono] using Core.HasType.letE valueTyped bodyTyped
  | case _ _ _ _ _ ihScrutinee ihMatch ihFail =>
    rename_i depth' env' scrutinee pattern onMatch onFail scrutineeType bindings resultType
      scrutineeTyped patternTyped bindingsScoped matchTyped failTyped
    cases fragment with
    | case scrutineeFragment patternFragment matchFragment failFragment =>
      have scrutineeCore := ihScrutinee scrutineeFragment monoEnv
      have patternCore :=
        PatTy.erase_runtimePat (coreSig := []) patternFragment patternTyped
      have branchMono : MonoTyEnv (bindings.map mono ++ env') := by
        intro scheme member
        simp only [List.mem_append] at member
        rcases member with member | member
        · obtain ⟨binding, _bindingMember, rfl⟩ := List.mem_map.mp member
          rfl
        · exact monoEnv scheme member
      have matchCore := ihMatch matchFragment branchMono
      have failCore := ihFail failFragment monoEnv
      have matchCore' :
          Core.HasType [] (bindings.map Ty.erase ++
            env'.map fun scheme => scheme.body.erase)
            onMatch.eraseMono resultType.erase := by
        simpa [List.map_append, mono, Ty.erase, Function.comp_def] using matchCore
      simpa [Expr.eraseMono, List.map_append, mono, Ty.erase] using
        Core.HasType.case scrutineeCore patternCore matchCore' failCore
  | construct => cases fragment
  | fail => cases fragment
  | raise => cases fragment

/-- Sûreté à fuel arbitraire pour le véritable évaluateur Core, avec des
liaisons locales monomorphes. Les environnements runtime sont reliés aux
schémas par `RuntimeEnvRel`; les résultats timeout, matchFail et error restent
autorisés comme dans `Core.Safe`. -/
theorem eval_safe_monoLetRuntimeFragment {sig : Signature} {env : TyEnv}
    {values : List Core.Val} {expr : Expr} {type : Ty}
    (envRel : RuntimeEnvRel values env)
    (typed : HasType sig 0 env expr type) (fragment : RuntimeFragment expr)
    (fuel : Nat) :
    Core.Safe [] (Core.eval fuel values expr.erase) type.erase := by
  have coreTyped := HasType.erase_runtimeFragment typed fragment envRel.monoTyEnv
  have coreEnv := envRel.coreEnvTy
  have coreTyped' : Core.HasType [] (env.map fun scheme => scheme.body.erase)
      expr.eraseMono type.erase := coreTyped
  have safe := Core.eval_safe fuel coreEnv coreTyped'
  exact (Expr.eval_eraseMono_eq_erase fuel values fragment) ▸ safe

/-- Régression concrète d'une liaison locale monomorphe dont le corps lit sa
valeur liée. -/
def boundIntLet : Expr :=
  .letE ⟨0, .int⟩ (.int 9) (.var 0 [])

theorem eval_safe_boundIntLet {sig : Signature} (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] boundIntLet.erase) .int := by
  have typed : HasType sig 0 [] boundIntLet .int := by
    apply HasType.letE (scheme := ⟨0, .int⟩)
    · simp [Scheme.wellScoped, Ty.wellScoped]
    · simpa [boundIntLet, TyEnv.weaken_zero] using
        (HasType.int : HasType sig 0 [] (.int 9) .int)
    · have hEnv : ([⟨0, .int⟩] : TyEnv)[0]? = some ⟨0, .int⟩ := rfl
      have hType : (⟨0, .int⟩ : Scheme).instantiate [] = some .int :=
        mono_instantiate .int
      exact HasType.var hEnv hType rfl
  have fragment : RuntimeFragment boundIntLet := by
    exact .letE rfl (.int 9) (.var 0)
  exact eval_safe_monoLetRuntimeFragment RuntimeEnvRel.nil typed fragment fuel

/-- Application d'une fermeture monomorphe qui capture une liaison de
l'environnement lexical ; la variable d'indice 1 est celle capturée. -/
def capturedIntLambdaApp : Expr :=
  .letE ⟨0, .int⟩ (.int 11)
    (.app (.lam .int (.var 1 [])) (.int 4))

theorem eval_safe_capturedIntLambdaApp {sig : Signature} (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] capturedIntLambdaApp.erase) .int := by
  have typed : HasType sig 0 [] capturedIntLambdaApp .int := by
    apply HasType.letE (scheme := ⟨0, .int⟩)
    · simp [Scheme.wellScoped, Ty.wellScoped]
    · simpa [TyEnv.weaken_zero] using
        (HasType.int : HasType sig 0 [] (.int 11) .int)
    · apply HasType.app
      · apply HasType.lam
        · simp [Ty.wellScoped]
        · have hEnv : ([mono .int, mono .int] : TyEnv)[1]? = some (mono .int) := rfl
          have hType : (mono .int).instantiate [] = some .int := mono_instantiate .int
          exact HasType.var hEnv hType (by simp)
      · exact HasType.int
  have fragment : RuntimeFragment capturedIntLambdaApp := by
    exact .letE rfl (.int 11)
      (.app (.lam (.var 1) rfl) (.int 4))
  exact eval_safe_monoLetRuntimeFragment RuntimeEnvRel.nil typed fragment fuel

/-- Le corps appliqué retrouve bien la valeur capturée par la fermeture. -/
theorem eval_capturedIntLambdaApp :
    Core.eval 20 [] capturedIntLambdaApp.erase = .ok (.int 11) := by
  rfl

/-- Récursion entière monomorphe utilisant le compteur et la fonction liée. -/
def recursiveCountdown : Expr :=
  .fix .int .int
    (.ite (.binop .eq (.var 0 []) (.int 0))
      (.int 0)
      (.app (.var 1 []) (.binop .sub (.var 0 []) (.int 1))))

def recursiveCountdownApplication : Expr :=
  .app recursiveCountdown (.int 3)

theorem eval_safe_recursiveCountdownApplication {sig : Signature} (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] recursiveCountdownApplication.erase) .int := by
  have typed : HasType sig 0 [] recursiveCountdownApplication .int := by
    have hN :
        HasType sig 0 [mono .int, mono (.arrow .int .int)] (.var 0 []) .int := by
      exact .var rfl (by simp [mono, Scheme.instantiate, Ty.subst])
        (by simp)
    have hRecursive :
        HasType sig 0 [mono .int, mono (.arrow .int .int)]
          (.var 1 []) (.arrow .int .int) := by
      exact .var (by rfl)
        (by simp [mono, Scheme.instantiate, Ty.subst])
        (by simp)
    apply HasType.app
    · apply HasType.fix
      · simp [Ty.wellScoped]
      · simp [Ty.wellScoped]
      · apply HasType.ite
        · exact HasType.binop (op := .eq) hN .int
        · exact .int
        · exact HasType.app hRecursive (HasType.binop (op := .sub) hN .int)
    · exact .int
  have fragment : RuntimeFragment recursiveCountdownApplication := by
    apply RuntimeFragment.app
    · apply RuntimeFragment.fix
      · apply RuntimeFragment.ite
        · exact .binop (.var 0) (.int 0)
        · exact .int 0
        · exact RuntimeFragment.app (.var 1) (.binop (.var 0) (.int 1))
      · rfl
    · exact .int 3
  exact eval_safe_monoLetRuntimeFragment RuntimeEnvRel.nil typed fragment fuel

theorem eval_recursiveCountdownApplication :
    Core.eval 100 [] recursiveCountdownApplication.erase = .ok (.int 0) := by
  rfl

/-- Le filtrage Core conserve l'ordre des liaisons d'un motif de paire. -/
def pairPatternCase : Expr :=
  .case (.pair (.int 7) (.bool true))
    (.pair .var (.bool true)) (.var 0 []) (.int 0)

theorem eval_safe_pairPatternCase {sig : Signature} (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] pairPatternCase.erase) .int := by
  have typed : HasType sig 0 [] pairPatternCase .int := by
    have scrutineeTyped :
        HasType sig 0 [] (.pair (.int 7) (.bool true)) (.prod .int .bool) :=
      .pair .int .bool
    have matchTyped : HasType sig 0 [mono .int] (.var 0 []) .int := by
      exact .var rfl (by simp [mono, Scheme.instantiate, Ty.subst]) (by simp)
    exact .case scrutineeTyped rfl
      (by simp [TyEnv.wellScoped, Scheme.wellScoped, Ty.wellScoped, mono])
      matchTyped .int
  have fragment : RuntimeFragment pairPatternCase := by
    exact RuntimeFragment.case
      (.pair (.int 7) (.bool true))
      (.pair .var (.bool true))
      (.var 0)
      (.int 0)
  exact eval_safe_monoLetRuntimeFragment RuntimeEnvRel.nil typed fragment fuel

theorem eval_pairPatternCase :
    Core.eval 20 [] pairPatternCase.erase = .ok (.int 7) := by
  rfl

/-- Le `let` monomorphe inutilisé reste également sûr à tout fuel. -/
def discardedIntLet : Expr :=
  .letE ⟨0, .int⟩ (.int 9) (.int 2)

theorem eval_safe_discardedIntLet {sig : Signature} (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] discardedIntLet.erase) .int := by
  have typed : HasType sig 0 [] discardedIntLet .int := by
    apply HasType.letE (scheme := ⟨0, .int⟩)
    · simp [Scheme.wellScoped, Ty.wellScoped]
    · simpa [discardedIntLet, TyEnv.weaken_zero] using
        (HasType.int : HasType sig 0 [] (.int 9) .int)
    · simpa [discardedIntLet] using
        (HasType.int : HasType sig 0 [⟨0, .int⟩] (.int 2) .int)
  have fragment : RuntimeFragment discardedIntLet := by
    exact .letE rfl (.int 9) (.int 2)
  exact eval_safe_monoLetRuntimeFragment RuntimeEnvRel.nil typed fragment fuel

theorem eval_safe_runtimeFragment {sig : Signature} {expr : Expr} {type : Ty}
    (typed : HasType sig 0 [] expr type) (fragment : RuntimeFragment expr)
    (fuel : Nat) :
    Core.Safe [] (Core.eval fuel [] expr.erase) type.erase :=
  eval_safe_monoLetRuntimeFragment RuntimeEnvRel.nil typed fragment fuel

end Hypomnesis.Core.Poly
