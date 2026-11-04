import Lean.Data.Json
import Hypomnesis.Core.Check
import Hypomnesis.Core.Eval
import Hypomnesis.Core.Records

/-!
# Décodage des certificats (HYP-026)

Traduit un certificat JSON (`certificate/1.0.0` ou `1.1.0`, émis par le compilateur Python)
en un terme du fragment formalisé, que **`typeOf` — prouvé correct et complet —
vérifie ensuite**. Ce décodeur n'est pas prouvé et n'en a pas besoin : il ne
fait que construire des termes, il ne décide rien. Un défaut ici peut faire
rejeter un programme correct, jamais accepter un programme mal typé.

Traduction :
* le programme devient une chaîne de `letE`, une par définition atteignable,
  terminée par le n-uplet des définitions racines (le programme, sans le
  prélude) ;
* **monomorphisation** : une définition polymorphe est spécialisée à chaque
  instanciation utilisée ; seules les définitions atteignables sont traduites
  (passe de collecte jusqu'au point fixe, puis émission dans l'ordre) ;
* types de données instanciés à la demande dans la signature ; n-uplets en
  paires imbriquées à droite ; fonctions et applications curryfiées ;
* `match` : `letE s (case (var 0) p₁ b₁ (… (fail t)))` ; une garde duplique la
  suite de la chaîne ; le type `t` est obtenu par `typeOf` ;
* `let rec` d'une seule fonction : `fix`.

Ce qui sort du fragment est signalé comme tel (`Err.unsupported`).
-/

namespace Hypomnesis.Certificate

open Lean (Json)
open Hypomnesis.Core

inductive Err where
  | malformed (msg : String)
  | unsupported (msg : String)
  | illTyped (msg : String)

def Err.message : Err → String
  | .malformed m => s!"certificat illisible : {m}"
  | .unsupported m => s!"hors du fragment vérifié : {m}"
  | .illTyped m => s!"rejeté par le vérificateur : {m}"

/-- Types du certificat : variables nommées, constructeurs appliqués. -/
inductive CTy where
  | var (name : String)
  | con (name : String) (args : List CTy)
  deriving Inhabited

partial def CTy.key : CTy → String
  | .var n => "'" ++ n
  | .con n [] => n
  | .con n args => n ++ "(" ++ ", ".intercalate (args.map CTy.key) ++ ")"

partial def CTy.subst (σ : List (String × CTy)) : CTy → CTy
  | .var n => (σ.lookup n).getD (.var n)
  | .con n args => .con n (args.map (CTy.subst σ))

structure Decl where
  kind : String
  /-- Gabarit de l'argument de chaque constructeur (paramètres nommés `$i`). -/
  ctors : Array (Option CTy)
  fields : Array (String × CTy) := #[]

structure Def where
  kind : String
  body : Json
  forallNames : List String
  /-- Nom global défini (`none` pour `let _ = …`). -/
  name : Option String

/-- Une instance à émettre : définition et arguments de type (clos). -/
structure Inst where
  defIdx : Nat
  args : List CTy
  key : String

structure St where
  decls : List (String × Decl) := []
  defs : Array Def := #[]
  sig : Array (List Ty) := #[]
  instKeys : Array String := #[]
  records : List (Nat × List (String × Ty)) := []
  collecting : Bool := true
  requests : Array Inst := #[]
  /-- Globales émises, dans l'ordre : clé d'instance et type. -/
  emitted : Array (String × Ty) := #[]

abbrev M := StateT St (Except Err)

-- Valeurs par défaut requises par `partial def` (jamais utilisées comme résultats).
instance : Inhabited Ty := ⟨.unit⟩
instance : Inhabited Pat := ⟨.wild⟩
instance : Inhabited Expr := ⟨.unit⟩
instance : Inhabited St := ⟨{}⟩
instance : Inhabited Def := ⟨⟨"", .null, [], none⟩⟩
instance : Inhabited Inst := ⟨⟨0, [], ""⟩⟩

def malformed {α} (msg : String) : M α := throw (.malformed msg)
def unsupported {α} (msg : String) : M α := throw (.unsupported msg)

-- ------------------------------------------------------------------ JSON

def field (j : Json) (k : String) : M Json :=
  match j.getObjVal? k with
  | .ok v => pure v
  | .error _ => malformed s!"champ « {k} » manquant"

def opt (j : Json) (k : String) : Option Json := (j.getObjVal? k).toOption

def str (j : Json) : M String :=
  match j.getStr? with | .ok s => pure s | .error e => malformed e

def nat (j : Json) : M Nat :=
  match j.getNat? with | .ok n => pure n | .error e => malformed e

def int (j : Json) : M Int :=
  match j.getInt? with | .ok n => pure n | .error e => malformed e

def bool (j : Json) : M Bool :=
  match j.getBool? with | .ok b => pure b | .error e => malformed e

def arr (j : Json) : M (List Json) :=
  match j.getArr? with | .ok a => pure a.toList | .error e => malformed e

def isNull : Json → Bool
  | .null => true
  | _ => false

partial def parseTy (j : Json) : M CTy := do
  if let some v := opt j "var" then return .var (← str v)
  if let some v := opt j "param" then return .var s!"${← nat v}"
  if let some c := opt j "con" then
    let args ← (← arr (← field j "args")).mapM parseTy
    return .con (← str c) args
  malformed "type invalide"

-- ----------------------------------------------------------------- types

mutual
  /-- Traduit un type clos ; les types de données deviennent des instances de la signature. -/
  partial def toTy : CTy → M Ty
    | .var n => unsupported s!"variable de type {n} non instanciée (polymorphisme)"
    | .con "int" [] => pure .int
    | .con "bool" [] => pure .bool
    | .con "float" [] => pure .float
    | .con "string" [] => pure .string
    | .con "unit" [] => pure .unit
    | .con "->" [a, b] => return .arrow (← toTy a) (← toTy b)
    | .con "*" args => do
      match (← args.mapM toTy).reverse with
      | [] => malformed "n-uplet vide"
      | last :: rest => return rest.foldl (fun acc t => .prod t acc) last
    | .con name args => return .data (← dataIndex name args)

  partial def dataIndex (name : String) (args : List CTy) : M Nat := do
    let key := (CTy.con name args).key
    let st ← get
    if let some i := st.instKeys.findIdx? (· == key) then return i
    let some decl := st.decls.lookup name | malformed s!"type inconnu {name}"
    let i := st.sig.size
    set { st with sig := st.sig.push [], instKeys := st.instKeys.push key }
    let σ := (List.range args.length).zip args |>.map fun (k, a) => (s!"${k}", a)
    if decl.kind == "record" then
      let fields ← decl.fields.toList.mapM fun (name, t) => do
        return (name, ← toTy (t.subst σ))
      modify fun st => { st with
        sig := st.sig.set! i [Records.payloadTy (fields.map (·.2))]
        records := (i, fields) :: st.records }
      return i
    let ctorTys ← decl.ctors.toList.mapM fun
      | none => pure Ty.unit
      | some t => toTy (t.subst σ)
    modify fun st => { st with sig := st.sig.set! i ctorTys }
    return i
end

-- ------------------------------------------------------------ expressions

/-- Portée de décodage. `levels[i]` est le niveau Lean (compté depuis le premier
lieur local) de la variable locale d'indice `i` du certificat ; `locals` est le
contexte de types des lieurs locaux Lean (le plus récent d'abord). -/
structure Scope where
  levels : List Nat := []
  depth : Nat := 0
  locals : List Ty := []
  subst : List (String × CTy) := []
  /-- Fonction récursive en cours de définition : son nom et son niveau. -/
  self : Option (String × Nat) := none

def Scope.push (sc : Scope) (t : Ty) (visible : Bool := true) : Scope :=
  { sc with
    levels := if visible then sc.depth :: sc.levels else sc.levels
    depth := sc.depth + 1
    locals := t :: sc.locals }

def Scope.var (sc : Scope) (level : Nat) : Expr := .var (sc.depth - 1 - level)

/-- Contexte de typage complet : lieurs locaux puis globales émises. -/
def context (sc : Scope) : M Ctx := do
  return sc.locals ++ (← get).emitted.toList.reverse.map (·.2)

def checkType (sc : Scope) (e : Expr) (what : String) : M Ty := do
  if (← get).collecting then return .unit
  match typeOf (← get).sig.toList (← context sc) e with
  | some t => pure t
  | none => throw (.illTyped what)

def parseArgs (sc : Scope) (j : Json) : M (List CTy) := do
  return (← (← arr j).mapM parseTy).map (CTy.subst sc.subst)

def instKey (defIdx : Nat) (args : List CTy) : String :=
  s!"{defIdx}<" ++ ", ".intercalate (args.map CTy.key) ++ ">"

def resolveGlobal (sc : Scope) (name : String) (args : List CTy) : M Expr := do
  if let some (self, level) := sc.self then
    if self == name && args.isEmpty then return sc.var level
  let st ← get
  let some defIdx := st.defs.findIdx? (·.name == some name) | malformed s!"globale inconnue {name}"
  let key := instKey defIdx args
  if st.collecting then
    unless st.requests.any (·.key == key) do
      set { st with requests := st.requests.push ⟨defIdx, args, key⟩ }
    return .var 0
  let some p := st.emitted.findIdx? (·.1 == key) | malformed s!"instance non émise {key}"
  return .var (sc.depth + (st.emitted.size - 1 - p))

def literal (j : Json) : M (Sum Expr String) := do
  match ← str (← field j "kind") with
  | "int" => return .inl (.int (← int (← field j "value")))
  | "bool" => return .inl (.bool (← bool (← field j "value")))
  | "float" =>
    let some bitsJ := opt j "bits" |
      unsupported "littéral float historique sans bits binary64 ; réexporter en 1.1.0"
    let bits ← nat bitsJ
    unless bits < 2 ^ 64 do malformed "bits binary64 hors limites"
    let f := Float.ofBits (UInt64.ofNat bits)
    if f.isNaN || f.isInf then malformed "littéral float non fini"
    match (← field j "value").getNum? with
    | .ok n =>
      unless f == n.toFloat do malformed "bits float incompatibles avec la valeur"
      return .inl (.float f)
    | .error e => malformed e
  | "string" => return .inl (.string (← str (← field j "value")))
  | "unit" => return .inl .unit
  | k => return .inr k

def tupleOf {α} (pair : α → α → α) (unit : α) : List α → α
  | [] => unit
  | [x] => x
  | x :: rest => pair x (tupleOf pair unit rest)

def recordFields (d : Nat) : M (List (String × Ty)) := do
  let some fields := (← get).records.lookup d | malformed "type record attendu"
  return fields

def namedFields (items : List Json) : M (List (String × Json)) := do
  let result ← items.mapM fun item => do return (← str (← field item "name"), item)
  let names := result.map (·.1)
  unless names.length == names.eraseDups.length do malformed "champs dupliqués"
  return result

partial def patternChoices (j : Json) : M (List Json) := do
  if let some choices := opt j "or" then
    let [left, right] ← arr choices | malformed "deux alternatives de motif attendues"
    return (← patternChoices left) ++ (← patternChoices right)
  return [j]

/-- Motif ; rend aussi les emplacements dans l'ordre d'occurrence. -/
partial def decPat (j : Json) (expected : Ty := .unit) : M (Pat × List Nat) := do
  if (opt j "wild").isSome then return (.wild, [])
  if let some k := opt j "bind" then return (.var, [← nat k])
  if let some l := opt j "lit" then
    match ← literal l with
    | .inl (.int n) => return (.int n, [])
    | .inl (.bool b) => return (.bool b, [])
    | .inl (.float f) => return (.float f, [])
    | .inl (.string s) => return (.string s, [])
    | .inl _ => return (.wild, [])
    | .inr k => unsupported s!"motif littéral {k}"
  if let some c := opt j "ctor" then
    let index ← nat (← field c "index")
    let arg ← field c "arg"
    if isNull arg then return (.ctor index .wild, [])
    let signature := (← get).sig
    let childTy := match expected with
      | .data d => ((signature[d]?).bind (·[index]?)).getD .unit
      | _ => .unit
    let (p, slots) ← decPat arg childTy
    return (.ctor index p, slots)
  if let some items := opt j "tuple" then
    let mut restTy := expected
    let entries ← arr items
    let mut parts := []
    for (item, i) in entries.zipIdx do
      let (childTy, tailTy) := if i + 1 == entries.length then (restTy, Ty.unit) else
        match restTy with | .prod a b => (a, b) | _ => (Ty.unit, Ty.unit)
      parts := parts ++ [← decPat item childTy]
      restTy := tailTy
    let pat := tupleOf Pat.pair .wild (parts.map (·.1))
    return (pat, (parts.map (·.2)).flatten)
  if (opt j "or").isSome then unsupported "motif alternatif (p | q)"
  if (opt j "alias").isSome then unsupported "motif alias (p as x)"
  if let some items := opt j "record" then
    let supplied ← namedFields (← arr items)
    if (← get).collecting then
      let parts ← supplied.mapM fun (_, item) => do decPat (← field item "pattern")
      return (.ctor 0 (parts.foldr (fun p rest => .pair p.1 rest) .wild),
        (parts.map (·.2)).flatten)
    let .data d := expected | malformed "motif record sur un type non record"
    let fields ← recordFields d
    unless supplied.all (fun (n, _) => fields.any (fun f => f.1 == n)) do
      malformed "champ inconnu dans un motif record"
    let parts ← fields.mapM fun (name, t) => do
      match supplied.lookup name with
      | none => pure (Pat.wild, [])
      | some item => do decPat (← field item "pattern") t
    return (.ctor 0 (parts.foldr (fun p rest => .pair p.1 rest) .wild),
      (parts.map (·.2)).flatten)
  malformed "motif invalide"

/-- Paramètres d'une fonction : types et corps. -/
def lamParts (sc : Scope) (j : Json) : M (List Ty × Json) := do
  let some lam := opt j "lam" | malformed "fonction attendue"
  let tys ← (← arr (← field lam "params")).mapM fun t => do toTy ((← parseTy t).subst sc.subst)
  return (tys, ← field lam "body")

mutual
  partial def dec (sc : Scope) (j : Json) : M Expr := do
    if let some l := opt j "lit" then
      match ← literal l with
      | .inl e => return e
      | .inr k => unsupported s!"littéral {k}"
    if let some v := opt j "local" then
      unless (← arr (← field v "type_args")).isEmpty do
        unsupported "polymorphisme local (instanciation d'une variable locale)"
      let i ← nat (← field v "index")
      let some level := sc.levels[i]? | malformed s!"indice local {i} hors de portée"
      return sc.var level
    if let some g := opt j "global" then
      return ← resolveGlobal sc (← str (← field g "name")) (← parseArgs sc (← field g "type_args"))
    if (opt j "lam").isSome then
      let (tys, body) ← lamParts sc j
      return ← decLams sc tys body
    if let some a := opt j "app" then
      let fn ← dec sc (← field a "fn")
      let args ← (← arr (← field a "args")).mapM (dec sc)
      return args.foldl Expr.app fn
    if let some l := opt j "let" then
      unless (← arr (← field l "forall")).isEmpty do unsupported "let polymorphe local"
      let t ← toTy ((← parseTy (← field l "value_type")).subst sc.subst)
      let value ← dec sc (← field l "value")
      return .letE value (← dec (sc.push t) (← field l "body"))
    if let some r := opt j "letrec" then
      unless (← arr (← field r "forall")).isEmpty do unsupported "let rec polymorphe local"
      let some b := (← arr (← field r "bindings")).head? | malformed "letrec vide"
      unless (← arr (← field r "bindings")).length == 1 do unsupported "récursion mutuelle"
      let t ← toTy ((← parseTy (← field b "type")).subst sc.subst)
      let fixE ← decFix sc t (← field b "lam") none
      return .letE fixE (← dec (sc.push t) (← field r "body"))
    if let some m := opt j "match" then
      unless (← arr (← field m "forall")).isEmpty do unsupported "let à motif polymorphe"
      return ← decMatch sc (← field m "scrutinee") (← arr (← field m "cases"))
    if let some items := opt j "tuple" then
      return tupleOf Expr.pair .unit (← (← arr items).mapM (dec sc))
    if let some c := opt j "construct" then
      let d ← dataIndex (← str (← field c "type")) (← parseArgs sc (← field c "type_args"))
      let arg ← field c "arg"
      let argE ← if isNull arg then pure Expr.unit else dec sc arg
      return .construct d (← nat (← field c "index")) argE
    if let some record := opt j "record" then
      let d ← dataIndex (← str (← field record "type")) (← parseArgs sc (← field record "type_args"))
      return ← decRecord sc d none (← arr (← field record "fields"))
    if let some update := opt j "update" then
      let base ← dec sc (← field update "base")
      let fields ← arr (← field update "fields")
      if (← get).collecting then
        for item in fields do discard <| dec sc (← field item "value")
        return .unit
      let .data d ← checkType sc base "base d'une mise à jour" | malformed "record attendu"
      return ← decRecord sc d (some base) fields
    if let some access := opt j "field" then
      let base ← dec sc (← field access "expr")
      if (← get).collecting then return .unit
      let .data d ← checkType sc base "accès à un champ" | malformed "record attendu"
      let fields ← recordFields d
      let name ← str (← field access "name")
      let some i := fields.findIdx? (fun f => f.1 == name) | malformed s!"champ inconnu {name}"
      return .app (Records.get d i fields[i]!.2) base
    malformed "expression invalide"

  partial def decRecord (sc : Scope) (d : Nat) (base : Option Expr)
      (items : List Json) : M Expr := do
    let fields ← recordFields d
    let supplied ← namedFields items
    unless supplied.all (fun (n, _) => fields.any (fun f => f.1 == n)) do
      malformed "champ record inconnu"
    if base.isNone && supplied.length != fields.length then malformed "champs record manquants"
    let mut inner := sc
    let mut chain : Array Expr := #[]
    let baseLevel := sc.depth
    if let some e := base then
      chain := chain.push e
      inner := inner.push (.data d) (visible := false)
    let mut levels : List (String × Nat) := []
    for (name, item) in supplied do
      let some t := fields.lookup name | malformed s!"champ inconnu {name}"
      chain := chain.push (← dec inner (← field item "value"))
      levels := (name, inner.depth) :: levels
      inner := inner.push t (visible := false)
    if base.isSome then
      inner := inner.push (Records.payloadTy (fields.map (·.2))) (visible := false)
    let values := fields.zipIdx |>.map fun ((name, _), i) =>
      match levels.lookup name with
      | some level => inner.var level
      | none => Records.project i (.var 0)
    let rebuilt := Expr.construct d 0 (Records.payload values)
    let body := if base.isSome then
      Expr.case (({inner with depth := inner.depth - 1} : Scope).var baseLevel)
        (.ctor 0 .var) rebuilt (.fail (.data d))
      else rebuilt
    return chain.foldr Expr.letE body

  partial def decLams (sc : Scope) (tys : List Ty) (body : Json) : M Expr := do
    match tys with
    | [] => dec sc body
    | t :: rest => return .lam t (← decLams (sc.push t) rest body)

  /-- `fix` pour une fonction récursive de type `t` (premier paramètre lié par
  `fix`, les suivants par des `lam`). `self` : nom global de la fonction, s'il
  s'agit d'une définition de premier niveau. -/
  partial def decFix (sc : Scope) (t : Ty) (lamJ : Json) (self : Option String) : M Expr := do
    let (tys, body) ← lamParts sc lamJ
    let .arrow dom cod := t | malformed "type de fonction récursive attendu"
    let some _ := tys.head? | malformed "fonction récursive sans paramètre"
    -- Contexte du corps de `fix` : [x, f, …] ; f au niveau sc.depth.
    let withF : Scope := match self with
      | some name => { sc.push t (visible := false) with self := some (name, sc.depth) }
      | none => sc.push t
    return .fix dom cod (← decLams (withF.push dom) tys.tail body)

  partial def decMatch (sc : Scope) (scrutJ : Json) (cases : List Json) : M Expr := do
    let scrut ← dec sc scrutJ
    let tx ← checkType sc scrut "type du filtré"
    let inner := sc.push tx (visible := false)
    let some first := cases.head? | malformed "match sans cas"
    -- Type du résultat : celui du corps du premier cas (pour le `fail` final).
    let resultT ← do
      let choices ← patternChoices (← field first "pattern")
      let some firstChoice := choices.head? | malformed "motif alternatif vide"
      let (pat, slots) ← decPat firstChoice tx
      let bodyScope ← caseScope inner tx pat slots
      checkType bodyScope (← dec bodyScope (← field first "body")) "corps d'un cas"
    return .letE scrut (← decCases inner (sc.depth) tx resultT cases)

  /-- Portée d'un cas : les variables du motif, emplacement 0 le plus ancien. -/
  partial def caseScope (sc : Scope) (tx : Ty) (pat : Pat) (slots : List Nat) : M Scope := do
    unless slots.mergeSort (· ≤ ·) == List.range slots.length do
      malformed "emplacements de variables de motif invalides"
    let bs ← if (← get).collecting then pure (slots.map fun _ => Ty.unit) else
      match patTypeOf (← get).sig.toList pat tx with
      | some bs => pure bs
      | none => throw (.illTyped "motif incompatible avec le filtré")
    let pushed := bs.reverse.foldl (fun s t => s.push t (visible := false)) sc
    let mut levels := []
    for slot in List.range slots.length do
      let some position := slots.findIdx? (· == slot) | malformed "emplacement de motif absent"
      levels := (sc.depth + position) :: levels
    return {pushed with levels := levels ++ sc.levels}

  partial def decCases (sc : Scope) (scrutLevel : Nat) (tx resultT : Ty)
      (cases : List Json) : M Expr := do
    match cases with
    | [] => return .fail resultT
    | c :: rest =>
      decChoices sc scrutLevel tx resultT (← patternChoices (← field c "pattern"))
        (← field c "guard") (← field c "body") rest none

  partial def decChoices (sc : Scope) (scrutLevel : Nat) (tx resultT : Ty)
      (choices : List Json) (guard bodyJ : Json) (rest : List Json)
      (bindings : Option (List (Option Ty))) : M Expr := do
    match choices with
    | [] => decCases sc scrutLevel tx resultT rest
    | choice :: choices =>
      let (pat, slots) ← decPat choice tx
      let bodyScope ← caseScope sc tx pat slots
      let signature := (bodyScope.levels.take slots.length).map fun level =>
        bodyScope.locals[bodyScope.depth - 1 - level]?
      if let some expected := bindings then
        unless signature == expected do
          throw (.illTyped "variables incompatibles entre alternatives de motif")
      let body ← dec bodyScope bodyJ
      let onFail ← decChoices sc scrutLevel tx resultT choices guard bodyJ rest (some signature)
      let onMatch ← if isNull guard then pure body else do
        let g ← dec bodyScope guard
        -- La suite, dupliquée sous les variables du motif (invisibles pour le certificat).
        let hidden : Scope := { bodyScope with levels := sc.levels }
        pure (.ite g body (← decCases hidden scrutLevel tx resultT rest))
      return .case (sc.var scrutLevel) pat onMatch onFail
end

-- ------------------------------------------------------------ définitions

/-- Primitives exprimables dans le fragment, à leur type instancié. -/
def native (symbol : String) (t : Ty) : M Expr := do
  if symbol == "core.failwith" then
    let .arrow .string result := t | unsupported "signature failwith"
    return .lam .string (.raise result (.var 0))
  let intOp := Ty.arrow .int (.arrow .int .int)
  let intCmp := Ty.arrow .int (.arrow .int .bool)
  let bin (op : BinOp) (swap : Bool := false) : Expr :=
    if swap then .binop op (.var 0) (.var 1) else .binop op (.var 1) (.var 0)
  let neg (e : Expr) : Expr := .ite e (.bool false) (.bool true)
  let body? : Option Expr :=
    if t == intOp then
      match symbol with
      | "int.add" => some (bin .add)
      | "int.sub" => some (bin .sub)
      | "int.mul" => some (bin .mul)
      | "int.div" => some (bin .div)
      | "int.mod" => some (bin .mod)
      | _ => none
    else if t == intCmp then
      match symbol with
      | "poly.eq" => some (bin .eq)
      | "poly.neq" => some (neg (bin .eq))
      | "poly.lt" => some (bin .lt)
      | "poly.gt" => some (bin .lt (swap := true))
      | "poly.le" => some (neg (bin .lt (swap := true)))
      | "poly.ge" => some (neg (bin .lt))
      | _ => none
    else if t == .arrow .float (.arrow .float .float) then
      match symbol with
      | "float.add" => some (bin .fadd)
      | "float.sub" => some (bin .fsub)
      | "float.mul" => some (bin .fmul)
      | "float.div" => some (bin .fdiv)
      | _ => none
    else if t == .arrow .float (.arrow .float .bool) then
      match symbol with
      | "poly.eq" => some (bin .feq)
      | "poly.neq" => some (neg (bin .feq))
      | "poly.lt" => some (bin .flt)
      | "poly.gt" => some (bin .flt (swap := true))
      | "poly.le" => some (bin .fle)
      | "poly.ge" => some (bin .fle (swap := true))
      | _ => none
    else if t == .arrow .float (.arrow .float .int) && symbol == "poly.compare" then
      some (bin .fcompare)
    else if t == .arrow .string (.arrow .string .string) && symbol == "string.concat" then
      some (bin .sconcat)
    else if t == .arrow .string (.arrow .string .bool) then
      match symbol with
      | "poly.eq" => some (bin .seq)
      | "poly.neq" => some (neg (bin .seq))
      | "poly.lt" => some (bin .slt)
      | "poly.gt" => some (bin .slt (swap := true))
      | "poly.le" => some (neg (bin .slt (swap := true)))
      | "poly.ge" => some (neg (bin .slt))
      | _ => none
    else if t == .arrow .string (.arrow .string .int) && symbol == "poly.compare" then
      some (bin .scompare)
    else none
  match body? with
  | some body =>
    let .arrow dom _ := t | unsupported "signature de primitive"
    return .lam dom (.lam dom body)
  | none => unsupported s!"primitive {symbol} au type {repr t}"

def parseDef (j : Json) : M Def := do
  if let some v := opt j "value" then
    let targets ← arr (← field v "targets")
    let pat ← field v "pattern"
    let name ← match targets with
      | [] => if (opt pat "wild").isSome then pure none else pure (some "")
      | [t] => pure (some (← str (← field t "name")))
      | _ => pure (some "")
    let forallNames ← (← arr (← field v "forall")).mapM str
    return ⟨"value", v, forallNames, name⟩
  if let some r := opt j "rec" then
    let bindings ← arr (← field r "bindings")
    let name ← match bindings with
      | [b] => pure (some (← str (← field b "name")))
      | _ => pure (some "")
    return ⟨"rec", r, ← (← arr (← field r "forall")).mapM str, name⟩
  if let some n := opt j "native" then
    return ⟨"native", n, ← (← arr (← field n "forall")).mapM str, some (← str (← field n "name"))⟩
  malformed "définition invalide"

/-- Décode une instance de définition : son terme et son type. -/
def decodeDef (d : Def) (args : List CTy) : M (Expr × Ty) := do
  let σ := d.forallNames.zip args
  let sc : Scope := { subst := σ }
  if d.name == some "" then unsupported "définition liant plusieurs noms (motif ou récursion mutuelle)"
  match d.kind with
  | "value" =>
    let pat ← field d.body "pattern"
    unless (opt pat "bind").isSome || (opt pat "wild").isSome do
      unsupported "définition par motif"
    let t ← toTy ((← parseTy (← field d.body "type")).subst σ)
    return (← dec sc (← field d.body "expr"), t)
  | "rec" =>
    let some b := (← arr (← field d.body "bindings")).head? | malformed "rec vide"
    let t ← toTy ((← parseTy (← field b "type")).subst σ)
    return (← decFix sc t (← field b "lam") d.name, t)
  | _ =>
    let t ← toTy ((← parseTy (← field d.body "type")).subst σ)
    return (← native (← str (← field d.body "symbol")) t, t)

structure Report where
  program : Expr
  sig : Sig
  type : Ty
  instances : Nat
  dataTypes : Nat
  skipped : List String

/-- Décode et **vérifie** un certificat. -/
def check (cert : Json) : Except Err Report := do
  let run : M Report := do
    let version ← str (← field cert "certificate_version")
    unless version == "1.0.0" || version == "1.1.0" do
      malformed s!"version de certificat inconnue {version}"
    for t in ← arr (← field cert "types") do
      let ctors ← (← arr (← field t "constructors")).mapM fun c => do
        let a ← field c "arg"
        let template ← if isNull a then pure none else some <$> parseTy a
        return (← nat (← field c "index"), template)
      let ordered := (ctors.toArray.qsort (·.1 < ·.1)).map (·.2)
      let fields ← namedFields (← arr (← field t "fields"))
      let recordTypes ← fields.mapM fun (name, item) => do
        return (name, ← parseTy (← field item "type"))
      let decl : Decl := ⟨← str (← field t "kind"), ordered, recordTypes.toArray⟩
      let name ← str (← field t "name")
      modify fun st => { st with decls := (name, decl) :: st.decls }
    let defs ← (← arr (← field cert "definitions")).mapM parseDef
    modify fun st => { st with defs := defs.toArray }
    let start ← match opt cert "program_start" with
      | some s => nat s
      | none => pure 0
    -- Racines : les définitions monomorphes du programme.
    let mut skipped := []
    for i in [start:defs.length] do
      let d := defs[i]!
      if d.forallNames.isEmpty then
        let key := instKey i []
        modify fun st => { st with requests := st.requests.push ⟨i, [], key⟩ }
      else
        skipped := skipped ++ [d.name.getD "_"]
    let roots := (← get).requests.size
    -- Passe 1 : collecte des instances atteignables, jusqu'au point fixe.
    let mut k := 0
    while k < (← get).requests.size do
      let inst := (← get).requests[k]!
      discard <| decodeDef ((← get).defs[inst.defIdx]!) inst.args
      k := k + 1
    -- Passe 2 : émission dans l'ordre des définitions.
    let insts := (← get).requests.qsort (·.defIdx < ·.defIdx)
    let rootKeys := ((← get).requests.extract 0 roots).map (·.key)
    modify fun st => { st with collecting := false }
    let mut chain : Array Expr := #[]
    for inst in insts do
      let (e, t) ← decodeDef ((← get).defs[inst.defIdx]!) inst.args
      unless (← checkType {} e "définition mal typée") == t do
        throw (.illTyped "annotation de définition incompatible avec son expression")
      chain := chain.push e
      modify fun st => { st with emitted := st.emitted.push (inst.key, t) }
    let st ← get
    let m := st.emitted.size
    let rootVars := rootKeys.toList.filterMap fun key =>
      (st.emitted.findIdx? (·.1 == key)).map fun p => Expr.var (m - 1 - p)
    let body := tupleOf Expr.pair .unit rootVars
    let program := chain.foldr Expr.letE body
    match typeOf st.sig.toList [] program with
    | some t => return ⟨program, st.sig.toList, t, m, st.sig.size, skipped⟩
    | none => throw (.illTyped "le programme n'est pas bien typé")
  return (← run.run {}).1

-- -------------------------------------------------------------- affichage

partial def showTy : Ty → String
  | .int => "int"
  | .bool => "bool"
  | .float => "float"
  | .string => "string"
  | .unit => "unit"
  | .arrow a b => s!"({showTy a} -> {showTy b})"
  | .prod a b => s!"({showTy a} * {showTy b})"
  | .data d => s!"data{d}"

partial def showVal : Val → String
  | .int n => toString n
  | .bool b => toString b
  | .float f => toString f
  | .string s => reprStr s
  | .unit => "()"
  | .clo .. | .rclo .. => "<fun>"
  | .pair a b => s!"({showVal a}, {showVal b})"
  | .con c v => s!"#{c} {showVal v}"

def showRes : Res → String
  | .ok v => showVal v
  | .stuck => "BLOQUÉ"
  | .timeout => "budget épuisé"
  | .matchFail => "Match_failure"
  | .error message => message

end Hypomnesis.Certificate
