"""Compare the proved structural JSON fragment with the actual typed boundary."""

import json
import random
import subprocess
from fractions import Fraction
from pathlib import Path

from hypomnesis.contracts.codec import CodecError, TypeCodec
from hypomnesis.runtime.values import RecordValue, Variant, from_iterable, iter_list
from hypomnesis.session import Session

FORMAL = Path(__file__).resolve().parents[2] / "formal"


def literal(value):
    return json.dumps(value, ensure_ascii=False)


def sequence(values):
    return "[" + ", ".join(values) + "]"


def signature(shape):
    if isinstance(shape, str):
        return shape
    kind, *args = shape
    if kind == "alias":
        return args[0]
    if kind in ("list", "option"):
        return f"({signature(args[0])}) {kind}"
    if kind == "pair":
        return f"({signature(args[0])}) * ({signature(args[1])})"
    return f"({signature(args[1][0][1])}) {args[0]}"


def type_term(shape):
    if isinstance(shape, str):
        return f"Ty.{shape}"
    kind, *args = shape
    if kind == "alias":
        return type_term(args[1])
    if kind in ("list", "option"):
        return f"(Ty.{kind} {type_term(args[0])})"
    if kind == "pair":
        return f"(Ty.pair {type_term(args[0])} {type_term(args[1])})"
    fields = sequence(f"({literal(k)}, {type_term(s)})" for k, s in args[1])
    return f"(Ty.record {literal(args[0])} {fields})"


def value_view(shape, value):
    if isinstance(shape, str):
        if shape == "unit":
            return ["unit"]
        return [shape, str(value) if shape == "int" else value]
    kind, *args = shape
    if kind == "alias":
        return value_view(args[1], value)
    if kind == "list":
        return ["list", [value_view(args[0], v) for v in iter_list(value)]]
    if kind == "pair":
        return ["pair", value_view(args[0], value[0]), value_view(args[1], value[1])]
    if kind == "option":
        return ["none"] if value.tag == "None" else ["some", value_view(args[0], value.arg)]
    return ["record", value.type_name, [[k, value_view(s, value.get(k))] for k, s in args[1]]]


def value_term(view):
    kind, *args = view
    if kind in ("unit", "none"):
        return f"Value.{kind}"
    if kind == "int":
        return f"(Value.int ({args[0]}))"
    if kind in ("bool", "string"):
        return f"(Value.{kind} {literal(args[0])})"
    if kind == "list":
        return f"(Value.list {sequence(value_term(v) for v in args[0])})"
    if kind == "pair":
        return f"(Value.pair {value_term(args[0])} {value_term(args[1])})"
    if kind == "some":
        return f"(Value.some {value_term(args[0])})"
    fields = sequence(f"({literal(k)}, {value_term(v)})" for k, v in args[1])
    return f"(Value.record {literal(args[0])} {fields})"


def json_view(value):
    if value is None:
        return ["null"]
    if type(value) is bool:
        return ["boolean", value]
    if type(value) in (int, float):
        q = Fraction(value)
        return ["number", str(q.numerator), str(q.denominator)]
    if isinstance(value, str):
        return ["string", value]
    if isinstance(value, list):
        return ["array", [json_view(v) for v in value]]
    return ["object", [[k, json_view(v)] for k, v in value.items()]]


def json_term(value):
    kind, *args = json_view(value)
    if kind == "null":
        return "Json.null"
    if kind == "number":
        return f"(Json.number (({args[0]} : Rat) / {args[1]}))"
    if kind in ("boolean", "string"):
        return f"(Json.{kind} {literal(args[0])})"
    if kind == "array":
        return f"(Json.array {sequence(json_term(v) for v in value)})"
    fields = sequence(f"({literal(k)}, {json_term(v)})" for k, v in value.items())
    return f"(Json.object {fields})"


def inline_schema(schema):
    def expand(node):
        if isinstance(node, list):
            return [expand(v) for v in node]
        if not isinstance(node, dict):
            return node
        node = {k: v for k, v in node.items() if k not in ("$schema", "$defs")}
        if "$ref" in node:
            assert set(node) == {"$ref"}
            return expand(schema["$defs"][node["$ref"].removeprefix("#/$defs/")])
        return {k: expand(v) for k, v in node.items()}

    return expand(schema)


RUNNER = """
import Hypomnesis.Contracts.Json
import Lean
open Hypomnesis.Contracts
set_option maxRecDepth 8192
set_option maxHeartbeats 8000000
def arr (xs : List Lean.Json) : Lean.Json := .arr xs.toArray
def str := Lean.Json.str
def obj := Lean.Json.mkObj
def closed (fs : List (String × Lean.Json)) : Lean.Json := obj [
  ("type", str "object"), ("properties", obj fs),
  ("required", arr (fs.map (fun p => str p.1))), ("additionalProperties", .bool false)]
mutual
 def schemaJson : Schema → Lean.Json
  | .null => obj [("type", str "null")]
  | .boolean => obj [("type", str "boolean")]
  | .integer => obj [("type", str "integer")]
  | .string => obj [("type", str "string")]
  | .array s => obj [("type", str "array"), ("items", schemaJson s)]
  | .pair a b => obj [
    ("type", str "array"), ("prefixItems", arr [schemaJson a, schemaJson b]),
    ("minItems", Lean.toJson (2 : Nat)), ("maxItems", Lean.toJson (2 : Nat)),
    ("items", .bool false)]
  | .optional s => obj [("oneOf", arr [
    closed [("tag", obj [("const", str "None")])],
    closed [("tag", obj [("const", str "Some")]), ("arg", schemaJson s)]])]
  | .object fs => closed (schemaFieldsJson fs)
 def schemaFieldsJson : List (String × Schema) → List (String × Lean.Json)
  | [] => []
  | (k, s) :: ss => (k, schemaJson s) :: schemaFieldsJson ss
end
mutual
 def valueJson : Value → Lean.Json
  | .unit => arr [str "unit"]
  | .bool b => arr [str "bool", .bool b]
  | .int n => arr [str "int", str n.repr]
  | .string s => arr [str "string", str s]
  | .list vs => arr [str "list", arr (valuesJson vs)]
  | .pair a b => arr [str "pair", valueJson a, valueJson b]
  | .none => arr [str "none"]
  | .some v => arr [str "some", valueJson v]
  | .record name fs =>
    arr [str "record", str name, arr (fieldsJson fs)]
 def valuesJson : List Value → List Lean.Json
  | [] => []
  | v :: vs => valueJson v :: valuesJson vs
 def fieldsJson : List (String × Value) → List Lean.Json
  | [] => []
  | (k, v) :: vs => arr [str k, valueJson v] :: fieldsJson vs
end
mutual
 def jsonJson : Json → Lean.Json
  | .null => arr [str "null"]
  | .boolean b => arr [str "boolean", .bool b]
  | .number q => arr [str "number", str q.num.repr, str q.den.repr]
  | .string s => arr [str "string", str s]
  | .array js => arr [str "array", arr (jsonItems js)]
  | .object fs => arr [str "object", arr (jsonFields fs)]
 def jsonItems : List Json → List Lean.Json
  | [] => []
  | j :: js => jsonJson j :: jsonItems js
 def jsonFields : List (String × Json) → List Lean.Json
  | [] => []
  | (k, j) :: js => arr [str k, jsonJson j] :: jsonFields js
end
def optionalJson : Option Value → Lean.Json
  | none => .null
  | some v => valueJson v
def result (sample : Ty × Value × List Json) : Lean.Json :=
  let (t, v, probes) := sample
  arr [jsonJson (encode v), optionalJson (decode t (encode v)), schemaJson (schemaOf t),
    arr (probes.map (fun j => optionalJson (decode t j)))]
"""


def corpus():
    rng = random.Random(43)
    scalars = [
        ("unit", ()),
        ("bool", True),
        ("bool", False),
        ("int", 0),
        ("int", 2**53 + 1),
        ("int", -(10**300 + 1)),
        ("string", 'é\n"x"'),
        ("string", ""),
    ]

    def sample(depth):
        if depth == 0:
            return rng.choice(scalars)
        kind = rng.choice(("scalar", "list", "pair", "option", "record"))
        if kind == "scalar":
            return rng.choice(scalars)
        child, value = sample(depth - 1)
        if kind == "list":
            return (kind, child), from_iterable([value] * rng.randrange(4))
        if kind == "pair":
            other, v = sample(depth - 1)
            return (kind, child, other), (value, v)
        if kind == "option":
            return (kind, child), Variant("Some", value, 1) if rng.randrange(2) else Variant("None")
        name = rng.choice(("Contract.box", "Contract.other"))
        fields = [("value", child), ("ok", "bool"), ("label", "string")]
        return (kind, name, fields), RecordValue(
            name, (("value", value), ("ok", True), ("label", "retained"))
        )

    return (
        scalars
        + [
            (("option", "unit"), Variant("Some", (), 1)),
            (("option", "unit"), Variant("None")),
            (("pair", "int", "bool"), (1, True)),
            (("list", "int"), from_iterable([0, -(10**300 + 1)])),
            (("alias", "integer", "int"), 10**300),
            (
                (
                    "alias",
                    "boxed_int",
                    (
                        "record",
                        "Contract.box",
                        [("value", "int"), ("ok", "bool"), ("label", "string")],
                    ),
                ),
                RecordValue("Contract.box", (("value", 7), ("ok", False), ("label", "alias"))),
            ),
        ]
        + [sample(3) for _ in range(82)]
    )


def test_json_roundtrip_schema_and_decoding_agree_with_the_proved_fragment(lean_lake, tmp_path):
    built = subprocess.run(
        [lean_lake, "build", "Hypomnesis.Contracts.Json"],
        cwd=FORMAL,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert built.returncode == 0, built.stdout + built.stderr
    session = Session()
    session.load("""
module Contract = struct
  type 'a box = { value : 'a; ok : bool; label : string }
  type 'a other = { value : 'a; ok : bool; label : string }
end
type integer = int
type boxed_int = int Contract.box
""")
    samples = corpus()
    assert len(samples) == 96
    for start in range(0, len(samples), 8):
        expected, cases = [], []
        for shape, value in samples[start : start + 8]:
            codec = TypeCodec(session.checker, signature(shape))
            encoded = json.loads(json.dumps(codec.encode(value), allow_nan=False))
            view = value_view(shape, value)
            probes = [encoded, {"unexpected": None}, None, True, 1.0, 1.5]
            if isinstance(encoded, dict):
                probes += [dict(reversed(encoded.items())), {**encoded, "extra": 0}]
                probes += [{k: v for k, v in encoded.items() if k != first} for first in encoded]
            elif isinstance(encoded, list):
                probes += [[*encoded, None], encoded[:-1]]
            decoded = []
            for probe in probes:
                try:
                    decoded.append(value_view(shape, codec.decode(probe)))
                except CodecError:
                    decoded.append(None)
            expected.append([json_view(encoded), view, inline_schema(codec.schema), decoded])
            cases.append(
                f"({type_term(shape)}, {value_term(view)}, "
                f"{sequence(json_term(probe) for probe in probes)})"
            )
        source = tmp_path / "Samples.lean"
        source.write_text(
            RUNNER
            + "\ndef cases : List (Ty × Value × List Json) := "
            + sequence(cases)
            + "\n#eval IO.println (arr (cases.map result)).compress\n",
            encoding="utf-8",
        )
        ran = subprocess.run(
            [lean_lake, "env", "lean", f"--root={tmp_path}", str(source)],
            cwd=FORMAL,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        assert ran.returncode == 0, ran.stdout + ran.stderr
        assert json.loads(ran.stdout) == expected
