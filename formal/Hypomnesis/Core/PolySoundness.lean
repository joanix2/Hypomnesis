import Hypomnesis.Core.Soundness
import Hypomnesis.Core.PolyTyping

/-! # Pont de sûreté polymorphe pour un fragment runtime monomorphe -/

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

/-- Sous-fragment fermé par les formes de contrôle et les `let` monomorphes ;
les variables sans argument de type ainsi que les lambdas et applications
monomorphes sont permises, mais pas la récursion, les constructions ni les
motifs. -/
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
  | fix => cases fragment
  | construct => cases fragment
  | case => cases fragment
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
