import Init.Data.Rat
import Std

/-! Typed structural JSON boundary, separate from Core evaluation.
Binary64, general variants and recursive schema references are not modeled. -/

namespace Hypomnesis.Contracts

inductive Json where
  | null
  | boolean (value : Bool)
  | number (value : Rat)
  | string (value : String)
  | array (items : List Json)
  | object (fields : List (String × Json))
  deriving Repr

inductive Ty where
  | unit | bool | int | string
  | list (item : Ty)
  | pair (left right : Ty)
  | option (item : Ty)
  | record (name : String) (fields : List (String × Ty))
  deriving Repr

inductive Value where
  | unit
  | bool (value : Bool)
  | int (value : Int)
  | string (value : String)
  | list (items : List Value)
  | pair (left right : Value)
  | none
  | some (value : Value)
  | record (name : String) (fields : List (String × Value))
  deriving Repr

mutual
  inductive ValTy : Value → Ty → Prop where
    | unit : ValTy .unit .unit
    | bool : ValTy (.bool b) .bool
    | int : ValTy (.int n) .int
    | string : ValTy (.string s) .string
    | list (items : ItemsTy vs t) : ValTy (.list vs) (.list t)
    | pair (left : ValTy a ta) (right : ValTy b tb) : ValTy (.pair a b) (.pair ta tb)
    | none : ValTy .none (.option t)
    | some (arg : ValTy v t) : ValTy (.some v) (.option t)
    | record (fields : FieldsTy vs ts) (distinct : (ts.map Prod.fst).Nodup) :
        ValTy (.record name vs) (.record name ts)

  inductive ItemsTy : List Value → Ty → Prop where
    | nil : ItemsTy [] t
    | cons (head : ValTy v t) (tail : ItemsTy vs t) : ItemsTy (v :: vs) t

  inductive FieldsTy : List (String × Value) → List (String × Ty) → Prop where
    | nil : FieldsTy [] []
    | cons (head : ValTy v t) (tail : FieldsTy vs ts) :
        FieldsTy ((name, v) :: vs) ((name, t) :: ts)
end

mutual
  def encode : Value → Json
    | .unit => .null
    | .bool b => .boolean b
    | .int n => .number n
    | .string s => .string s
    | .list vs => .array (encodeItems vs)
    | .pair a b => .array [encode a, encode b]
    | .none => .object [("tag", .string "None")]
    | .some v => .object [("tag", .string "Some"), ("arg", encode v)]
    | .record _ vs => .object (encodeFields vs)

  def encodeItems : List Value → List Json
    | [] => []
    | v :: vs => encode v :: encodeItems vs

  def encodeFields : List (String × Value) → List (String × Json)
    | [] => []
    | (name, v) :: vs => (name, encode v) :: encodeFields vs
end

def pop (key : String) : List (String × Json) → Option (Json × List (String × Json))
  | [] => none
  | (name, value) :: rest =>
    if key == name then some (value, rest)
    else do
      let (found, remaining) ← pop key rest
      pure (found, (name, value) :: remaining)

mutual
  def decode : Ty → Json → Option Value
    | .unit, .null => some .unit
    | .bool, .boolean b => some (.bool b)
    | .int, .number n => if n.den == 1 then some (.int n.num) else none
    | .string, .string s => some (.string s)
    | .list t, .array vs => Value.list <$> decodeItems t vs
    | .pair ta tb, .array [a, b] => do
      let va ← decode ta a
      let vb ← decode tb b
      pure (.pair va vb)
    | .option t, .object fs => do
      let (tag, rest) ← pop "tag" fs
      match tag, rest with
      | .string "None", [] => pure .none
      | .string "Some", [("arg", arg)] => Value.some <$> decode t arg
      | _, _ => none
    | .record name ts, .object fs => Value.record name <$> decodeFields ts fs
    | _, _ => none
  termination_by t j => (sizeOf t, sizeOf j)

  def decodeItems (t : Ty) : List Json → Option (List Value)
    | [] => some []
    | j :: js => do
      let v ← decode t j
      let vs ← decodeItems t js
      pure (v :: vs)
  termination_by js => (sizeOf t, sizeOf js)

  def decodeFields : List (String × Ty) → List (String × Json) →
      Option (List (String × Value))
    | [], [] => some []
    | [], _ :: _ => none
    | (name, t) :: ts, fs => do
      let (j, rest) ← pop name fs
      let v ← decode t j
      let vs ← decodeFields ts rest
      pure ((name, v) :: vs)
  termination_by ts _ => (sizeOf ts, 0)
end

mutual
  theorem decode_encode (typed : ValTy v t) : decode t (encode v) = some v := by
    cases typed with
    | unit => simp [decode, encode]
    | bool => simp [decode, encode]
    | int => simp [decode, encode]
    | string => simp [decode, encode]
    | list h => simp [encode, decode, decodeItems_encode h]
    | pair ha hb => simp [encode, decode, decode_encode ha, decode_encode hb]
    | none => simp [encode, decode, pop]
    | some h => simp [encode, decode, pop, decode_encode h]
    | record h _ => simp [encode, decode, decodeFields_encode h]

  theorem decodeItems_encode (typed : ItemsTy vs t) :
      decodeItems t (encodeItems vs) = some vs := by
    cases typed with
    | nil => simp [decodeItems, encodeItems]
    | cons h ht =>
      simp [encodeItems, decodeItems, decode_encode h, decodeItems_encode ht]

  theorem decodeFields_encode (typed : FieldsTy vs ts) :
      decodeFields ts (encodeFields vs) = some vs := by
    cases typed with
    | nil => simp [decodeFields, encodeFields]
    | cons h ht =>
      simp [encodeFields, decodeFields, pop, decode_encode h, decodeFields_encode ht]
end

inductive Schema where
  | null | boolean | integer | string
  | array (items : Schema)
  | pair (left right : Schema)
  | optional (arg : Schema)
  | object (properties : List (String × Schema))
  deriving Repr

mutual
  def schemaOf : Ty → Schema
    | .unit => .null
    | .bool => .boolean
    | .int => .integer
    | .string => .string
    | .list t => .array (schemaOf t)
    | .pair a b => .pair (schemaOf a) (schemaOf b)
    | .option t => .optional (schemaOf t)
    | .record _ fields => .object (schemaFields fields)

  def schemaFields : List (String × Ty) → List (String × Schema)
    | [] => []
    | (name, t) :: ts => (name, schemaOf t) :: schemaFields ts
end

mutual
  /-- `object` requires exactly the declared keys, irrespective of their order.
  `optional` abbreviates two closed, disjoint tagged-object branches of oneOf. -/
  inductive Conforms : Json → Schema → Prop where
    | null : Conforms .null .null
    | boolean : Conforms (.boolean b) .boolean
    | integer (integral : q.den = 1) : Conforms (.number q) .integer
    | string : Conforms (.string s) .string
    | array (items : ∀ j ∈ js, Conforms j s) : Conforms (.array js) (.array s)
    | pair (left : Conforms a sa) (right : Conforms b sb) :
        Conforms (.array [a, b]) (.pair sa sb)
    | none (order : fs.Perm [("tag", .string "None")]) :
        Conforms (.object fs) (.optional s)
    | some (order : fs.Perm [("tag", .string "Some"), ("arg", j)]) (arg : Conforms j s) :
        Conforms (.object fs) (.optional s)
    | object (keys : (fs.map Prod.fst).Perm (ss.map Prod.fst))
        (distinct : (fs.map Prod.fst).Nodup)
        (properties : ∀ name j, (name, j) ∈ fs → Property name j ss) :
        Conforms (.object fs) (.object ss)

  inductive Property : String → Json → List (String × Schema) → Prop where
    | here (value : Conforms j s) : Property name j ((name, s) :: ss)
    | there (value : Property name j ss) : Property name j ((other, s) :: ss)
end

theorem schemaFields_keys (ts : List (String × Ty)) :
    (schemaFields ts).map Prod.fst = ts.map Prod.fst := by
  induction ts with
  | nil => rfl
  | cons field ts ih => simp [schemaFields, ih]

mutual
  theorem encode_conforms (typed : ValTy v t) : Conforms (encode v) (schemaOf t) := by
    cases typed with
    | unit => exact .null
    | bool => exact .boolean
    | int => exact .integer rfl
    | string => exact .string
    | list h => exact .array (encodeItems_conform h)
    | pair ha hb => exact .pair (encode_conforms ha) (encode_conforms hb)
    | none => exact .none (.refl _)
    | some h => exact .some (.refl _) (encode_conforms h)
    | record h hd =>
      have fields := encodeFields_conform h
      apply Conforms.object
      · rw [fields.1, schemaFields_keys]
      · simpa [fields.1] using hd
      · exact fields.2

  theorem encodeItems_conform (typed : ItemsTy vs t) :
      ∀ j ∈ encodeItems vs, Conforms j (schemaOf t) := by
    cases typed with
    | nil => simp [encodeItems]
    | cons h ht =>
      intro j hj
      simp only [encodeItems, List.mem_cons] at hj
      cases hj with
      | inl he => subst j; exact encode_conforms h
      | inr hm => exact encodeItems_conform ht j hm

  theorem encodeFields_conform (typed : FieldsTy vs ts) :
      (encodeFields vs).map Prod.fst = ts.map Prod.fst ∧
      ∀ name j, (name, j) ∈ encodeFields vs →
        Property name j (schemaFields ts) := by
    cases typed with
    | nil => simp [encodeFields]
    | cons h ht =>
      have tail := encodeFields_conform ht
      constructor
      · exact congrArg (List.cons _) tail.1
      · intro key j hj
        simp only [encodeFields, List.mem_cons] at hj
        cases hj with
        | inl he =>
          cases he
          exact .here (encode_conforms h)
        | inr hm => exact .there (tail.2 key j hm)
end

end Hypomnesis.Contracts
