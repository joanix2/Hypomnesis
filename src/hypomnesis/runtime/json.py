"""Shared JSON boundary representations; no domain concepts or effect execution."""

from __future__ import annotations

import math
from typing import Any

from hypomnesis.language.errors import EvaluationError
from hypomnesis.runtime.values import NIL, RecordValue, Value, Variant, from_iterable

_TAGS = {"Null": 0, "Bool": 1, "Num": 2, "Str": 3, "Arr": 4, "Obj": 5, "Int": 6}


def json_variant(tag: str, arg: Value = None) -> Variant:
    return Variant(tag, arg, _TAGS[tag])


def list_items(value: Value) -> list[Value]:
    result, seen = [], set()
    while isinstance(value, Variant) and value.tag == "::":
        if id(value) in seen or type(value.arg) is not tuple or len(value.arg) != 2:
            raise EvaluationError("JSON: malformed or cyclic list")
        seen.add(id(value))
        head, value = value.arg
        result.append(head)
    if value != NIL:
        raise EvaluationError("JSON: list must terminate in []")
    return result


def value_to_data(value: Value) -> Any:
    """Structural encoding: even option constructors retain their tags."""
    if type(value) in (bool, int, str):
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise EvaluationError("JSON: non-finite number")
        return value
    if type(value) is tuple:
        return [value_to_data(v) for v in value] if value else None
    if isinstance(value, RecordValue):
        if len({k for k, _ in value.fields}) != len(value.fields):
            raise EvaluationError("JSON: duplicate record field")
        return {k: value_to_data(v) for k, v in value.fields}
    if isinstance(value, Variant):
        if value.tag in ("[]", "::"):
            return [value_to_data(v) for v in list_items(value)]
        result = {"tag": value.tag}
        if value.arg is not None:
            result["arg"] = value_to_data(value.arg)
        return result
    raise EvaluationError(f"JSON: value has no data representation: {type(value).__name__}")


def data_to_json(value: Any) -> Variant:
    """JSON data → Json.t, preserving integer and floating-point representations."""
    if value is None:
        return json_variant("Null")
    if type(value) is bool:
        return json_variant("Bool", value)
    if type(value) is int:
        return json_variant("Int", value)
    if type(value) is float:
        if not math.isfinite(value):
            raise EvaluationError("JSON: non-finite number")
        return json_variant("Num", value)
    if type(value) is str:
        return json_variant("Str", value)
    if type(value) is list:
        return json_variant("Arr", from_iterable(data_to_json(v) for v in value))
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            raise EvaluationError("JSON: object keys must be strings")
        return json_variant("Obj", from_iterable((k, data_to_json(v)) for k, v in value.items()))
    raise EvaluationError(f"JSON: not JSON data: {type(value).__name__}")


def json_to_data(value: Variant) -> Any:
    """Json.t → JSON data; reject malformed values rather than coerce them."""
    if not isinstance(value, Variant):
        raise EvaluationError("JSON: Json.t expected")
    if value.tag == "Null" and value.arg is None:
        return None
    expected = {"Bool": bool, "Str": str, "Num": float, "Int": int}
    if value.tag in expected and type(value.arg) is expected[value.tag]:
        if value.tag == "Num" and not math.isfinite(value.arg):
            raise EvaluationError("JSON: non-finite number")
        return value.arg
    if value.tag == "Arr":
        return [json_to_data(v) for v in list_items(value.arg)]
    if value.tag == "Obj":
        result = {}
        for pair in list_items(value.arg):
            if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
                raise EvaluationError("JSON: string/value pair expected")
            key, child = pair
            if key in result:
                raise EvaluationError(f"JSON: duplicate object key {key!r}")
            result[key] = json_to_data(child)
        return result
    raise EvaluationError(f"JSON: malformed Json.{value.tag}")
