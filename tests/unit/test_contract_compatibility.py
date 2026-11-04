"""Directional inclusion and preparation never import extension backends."""

from copy import deepcopy

import pytest
from hypothesis import given
from hypothesis import strategies as st

from hypomnesis.contracts.codec import TypeCodec, UnsupportedTypeError
from hypomnesis.contracts.compatibility import (
    CompatibilityError,
    UnsupportedSchemaError,
    require_inclusion,
)
from hypomnesis.contracts.registry import ContractError, SchemaRegistry
from hypomnesis.engine.registry import ExtensionRegistry
from hypomnesis.session import Session


@pytest.fixture(scope="module")
def checker():
    session = Session()
    session.check("""
type record = { count : int; name : string }
type tree = Leaf | Node of tree list
""")
    return session.checker


@pytest.mark.parametrize(
    "signature",
    [
        "int",
        "float",
        "string",
        "bool",
        "unit",
        "record",
        "tree",
        "int list",
        "unit option option",
        "int * string",
    ],
)
def test_generated_schemas_are_compatible_with_themselves(checker, signature):
    schema = TypeCodec(checker, signature).schema
    require_inclusion(schema, deepcopy(schema), SchemaRegistry())


@given(st.integers(-1000, 1000), st.integers(0, 1000))
def test_numeric_inclusion_direction(low, width):
    narrower = {"type": "integer", "minimum": low, "maximum": low + width}
    broader = {"type": "number", "minimum": low - 1, "maximum": low + width + 1}
    require_inclusion(narrower, broader, SchemaRegistry())
    with pytest.raises(CompatibilityError):
        require_inclusion(broader, narrower, SchemaRegistry())


@pytest.mark.parametrize(
    "source,target",
    [
        ({"type": "integer"}, {"type": "string"}),
        ({"type": "number"}, {"type": "integer"}),
        ({"type": "integer"}, {"type": "integer", "minimum": 0}),
        ({"type": "integer", "minimum": 0}, {"type": "integer", "exclusiveMinimum": 0}),
        ({"type": "string"}, {"type": "string", "minLength": 1}),
        ({"type": "string"}, {"type": "string", "enum": ["x"]}),
        ({"type": "string", "const": "x"}, {"type": "integer"}),
        (
            {"type": "array", "items": {"type": "integer"}},
            {"type": "array", "items": {"type": "string"}},
        ),
        (
            {"type": "array", "items": {"type": "integer"}},
            {"type": "array", "items": {"type": "integer"}, "maxItems": 1},
        ),
    ],
)
def test_incompatible_schemas_refused(source, target):
    with pytest.raises(CompatibilityError):
        require_inclusion(source, target, SchemaRegistry())


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "string", "pattern": "x"},
        {"type": "object", "additionalProperties": True},
        {"type": ["string", "null"]},
        {"oneOf": [{"type": "integer"}, {"type": "number"}]},
        {"allOf": [{"type": "integer"}]},
        {"$ref": "#/$defs/a", "type": "integer", "$defs": {"a": {"type": "integer"}}},
        {"$ref": "#"},
    ],
)
def test_unverifiable_is_not_reported_as_compatible(schema):
    with pytest.raises(UnsupportedSchemaError):
        require_inclusion(schema, schema, SchemaRegistry())


def test_known_references_only_and_schema_inspection_is_isolated():
    original = {"$id": "urn:integer", "type": "integer"}
    registry = SchemaRegistry([original])
    original["type"] = "string"
    require_inclusion({"$ref": "urn:integer"}, {"type": "number"}, registry)
    require_inclusion({"enum": [1, 2]}, {"$ref": "urn:integer"}, registry)
    with pytest.raises(ContractError, match="unknown schema"):
        require_inclusion({"$ref": "https://must-not-be-fetched.invalid"}, {}, registry)
    document = registry.schema("urn:integer")
    document["type"] = "string"
    assert registry.schema("urn:integer")["type"] == "integer"


def test_objects_and_tuple_direction(checker):
    record = TypeCodec(checker, "record").schema
    missing = deepcopy(record)
    missing["$defs"]["t0"]["required"] = ["name"]
    require_inclusion(record, missing, SchemaRegistry())
    with pytest.raises(CompatibilityError, match="required"):
        require_inclusion(missing, record, SchemaRegistry())
    tuple_schema = TypeCodec(checker, "int * int").schema
    array = {"type": "array", "items": {"type": "integer"}}
    require_inclusion(tuple_schema, array, SchemaRegistry())
    with pytest.raises(CompatibilityError):
        require_inclusion(array, tuple_schema, SchemaRegistry())


def test_prepare_refuses_before_import_and_returns_boundary_codecs(
    checker, extension_manifest, trapped_backend
):
    manifest = extension_manifest(signature={"input": "int", "output": "int"})
    schemas = SchemaRegistry.with_builtin_schemas()
    schemas.add({"$id": manifest["input_schema"], "type": "number"})
    schemas.add({"$id": manifest["output_schema"], "type": "integer", "minimum": 0})
    registry = ExtensionRegistry([manifest], schemas=schemas)
    prepared = registry.prepare("sample", checker)
    assert prepared.input.encode(3) == 3
    assert prepared.output.decode(3) == 3
    assert prepared.encode_input(3) == 3
    assert prepared.decode_output(3) == 3
    with pytest.raises(ContractError):
        prepared.decode_output(-1)
    prepared.manifest["signature"]["input"] = "changed"
    assert registry.show("sample")["signature"]["input"] == "int"
    bad = extension_manifest("bad", signature={"input": "string", "output": "int"})
    registry.add(bad)
    with pytest.raises(CompatibilityError):
        registry.prepare("bad", checker)
    assert not trapped_backend.exists()


def test_prepare_missing_schema_invalid_signature_and_independent_inspection(
    checker, extension_manifest, trapped_backend
):
    registry = ExtensionRegistry([extension_manifest()])
    assert registry.show("sample")
    with pytest.raises(ContractError, match="unknown schema"):
        registry.prepare("sample", checker)
    registry.add(extension_manifest("unknown", signature={"input": "unknown", "output": "int"}))
    with pytest.raises(UnsupportedTypeError):
        registry.prepare("unknown", checker)


def test_output_contract_must_not_be_broader_than_the_type(
    checker, extension_manifest, trapped_backend
):
    manifest = extension_manifest(signature={"input": "int", "output": "int"})
    schemas = SchemaRegistry.with_builtin_schemas()
    schemas.add({"$id": manifest["input_schema"], "type": "integer"})
    schemas.add({"$id": manifest["output_schema"], "type": "number"})
    registry = ExtensionRegistry([manifest], schemas=schemas)
    with pytest.raises(CompatibilityError):
        registry.prepare("sample", checker)


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "array", "items": {"$id": "urn:nested", "type": "integer"}},
        {"$ref": "relative.json"},
        {"$schema": "http://json-schema.org/draft-07/schema#", "type": "integer"},
        {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$ref": "#/$defs/a",
            "$defs": {"a": {"type": "integer"}},
        },
        {
            "type": "array",
            "items": {"$id": "urn:nested", "$ref": "#/$defs/a"},
            "$defs": {"a": {"type": "integer"}},
        },
    ],
)
def test_unmodeled_reference_scoping_is_refused(schema):
    with pytest.raises(UnsupportedSchemaError):
        require_inclusion(schema, schema, SchemaRegistry())


def test_float_output_requires_provably_finite_range(checker):
    codec = TypeCodec(checker, "float")
    require_inclusion(codec.schema, {"type": "number"}, SchemaRegistry())
    with pytest.raises(CompatibilityError):
        require_inclusion({"type": "number"}, codec.schema, SchemaRegistry())


def test_reference_resolution_for_finite_enum_is_offline_and_structural():
    registry = SchemaRegistry([{"$id": "urn:item", "type": "integer"}])
    target = {"type": "array", "items": {"$ref": "urn:item"}}
    require_inclusion({"const": [1, 2]}, target, registry)
    with pytest.raises(CompatibilityError):
        require_inclusion({"const": [1, "wrong"]}, target, registry)


def test_recursive_variants_with_different_branch_orders(checker):
    schema = TypeCodec(checker, "tree").schema
    reordered = deepcopy(schema)
    reordered["$defs"]["t0"]["oneOf"].reverse()
    require_inclusion(schema, reordered, SchemaRegistry())
    require_inclusion(reordered, schema, SchemaRegistry())


@pytest.mark.parametrize("pointer", ["minimum", "oneOf/-1", "oneOf/01"])
def test_invalid_reference_targets_are_explicit_errors(pointer):
    schema = {
        "$ref": "#/$defs/a/" + pointer,
        "$defs": {
            "a": {
                "type": "integer",
                "minimum": 0,
                "oneOf": [{"type": "integer"}, {"type": "string"}],
            }
        },
    }
    with pytest.raises(CompatibilityError):
        require_inclusion(schema, schema, SchemaRegistry())
