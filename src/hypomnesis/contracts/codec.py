"""Typed, reversible JSON boundary for closed Hypomnesis data types (ADR 0010)."""

from __future__ import annotations

import math
import sys
from copy import deepcopy
from typing import Any, NoReturn

from jsonschema import Draft202012Validator

from hypomnesis.language.errors import HypomnesisError
from hypomnesis.language.typesystem.infer import Checker, TypeInfo
from hypomnesis.language.typesystem.types import TCon, TVar, Type, substitute
from hypomnesis.runtime.values import NIL, RecordValue, Value, Variant, from_iterable

DRAFT = "https://json-schema.org/draft/2020-12/schema"
_SCALARS = {
    "int": "integer",
    "float": "number",
    "string": "string",
    "bool": "boolean",
    "unit": "null",
}


class CodecError(ValueError):
    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"{path}: {message}")
        self.path = path


class UnsupportedTypeError(CodecError):
    pass


def closed_type(t: Type) -> TCon:
    """Read bound variables without path compression or other checker mutation."""
    if isinstance(t, TVar) and t.ref is not None:
        return closed_type(t.ref)
    if not isinstance(t, TCon):
        raise UnsupportedTypeError("$", "open type has no JSON contract")
    return TCon(t.name, tuple(closed_type(arg) for arg in t.args))


class TypeCodec:
    def __init__(self, checker: Checker, type_: Type | str) -> None:
        try:
            resolved = checker.resolve_type(type_) if isinstance(type_, str) else type_
        except HypomnesisError as exc:
            raise UnsupportedTypeError("$", f"invalid signature: {exc}") from exc
        self.type = closed_type(resolved)
        self._types = deepcopy(checker.types_by_qname)
        self._definitions: dict[str, Any] = {}
        self._keys: dict[TCon, str] = {}
        self._active: dict[str, TCon] = {}
        root = self._schema(self.type)
        self._schema_document = {"$schema": DRAFT, **root}
        if self._definitions:
            self._schema_document["$defs"] = self._definitions
        Draft202012Validator.check_schema(self._schema_document)
        self._validator = Draft202012Validator(self._schema_document)

    @property
    def schema(self) -> dict[str, Any]:
        return deepcopy(self._schema_document)

    def _info(self, t: TCon) -> TypeInfo:
        info = self._types.get(t.name)
        if info is None or info.arity != len(t.args):
            raise UnsupportedTypeError("$", f"unknown type or invalid arity: {t.name}")
        return info

    @staticmethod
    def _object(properties: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties),
            "additionalProperties": False,
        }

    def _schema(self, t: TCon) -> dict[str, Any]:
        if t.name in _SCALARS and not t.args:
            if t.name == "float":
                return {
                    "type": "number",
                    "minimum": -sys.float_info.max,
                    "maximum": sys.float_info.max,
                }
            return {"type": _SCALARS[t.name]}
        if t.name == "list" and len(t.args) == 1:
            return {"type": "array", "items": self._schema(closed_type(t.args[0]))}
        if t.name == "*":
            return {
                "type": "array",
                "prefixItems": [self._schema(closed_type(a)) for a in t.args],
                "minItems": len(t.args),
                "maxItems": len(t.args),
                "items": False,
            }
        info = self._info(t)
        if info.kind == "alias" and info.alias is not None:
            return self._schema(closed_type(substitute(info.alias, t.args)))
        if info.kind not in ("record", "variant"):
            raise UnsupportedTypeError("$", f"type {t.name} has no data representation")
        previous = self._active.get(t.name)
        if previous is not None and previous != t:

            def contains(parent: Type) -> bool:
                return parent == t or (
                    isinstance(parent, TCon) and any(contains(a) for a in parent.args)
                )

            if not any(contains(a) for a in previous.args):
                raise UnsupportedTypeError("$", f"non-regular recursive type: {t.name}")
        if t in self._keys:
            return {"$ref": f"#/$defs/{self._keys[t]}"}
        key = f"t{len(self._keys)}"
        self._keys[t] = key
        self._active[t.name] = t
        self._definitions[key] = {}
        if info.kind == "record":
            body = self._object(
                {f.name: self._schema(closed_type(substitute(f.type, t.args))) for f in info.fields}
            )
        else:
            branches = []
            for ctor in info.ctors:
                properties: dict[str, Any] = {"tag": {"const": ctor.name}}
                if ctor.arg is not None:
                    properties["arg"] = self._schema(closed_type(substitute(ctor.arg, t.args)))
                branches.append(self._object(properties))
            body = {"oneOf": branches}
        self._definitions[key] = body
        if previous is None:
            del self._active[t.name]
        else:
            self._active[t.name] = previous
        return {"$ref": f"#/$defs/{key}"}

    def encode(self, value: Value) -> Any:
        result = self._convert(self.type, value, "$", encode=True)
        self._validate(result)
        return result

    def decode(self, value: Any) -> Value:
        self._validate(value)
        return self._convert(self.type, value, "$", encode=False)

    def _validate(self, value: Any) -> None:
        error = next(self._validator.iter_errors(value), None)
        if error is not None:
            raise CodecError(error.json_path, error.message)

    def _convert(self, t: TCon, value: Any, path: str, *, encode: bool) -> Any:
        def fail(message: str) -> NoReturn:
            raise CodecError(path, message)

        def convert(child: Type, v: Any, suffix: str) -> Any:
            return self._convert(closed_type(child), v, path + suffix, encode=encode)

        if t.name in _SCALARS:
            if t.name == "unit":
                if encode:
                    return None if type(value) is tuple and value == () else fail("unit expected")
                return () if value is None else fail("null expected")
            expected = {"int": int, "float": float, "string": str, "bool": bool}[t.name]
            if t.name == "int" and not encode and type(value) is float:
                if math.isfinite(value) and value.is_integer():
                    return int(value)
                return fail("mathematical integer expected")
            if t.name == "float":
                if type(value) not in ((float,) if encode else (int, float)):
                    return fail("finite float expected")
                try:
                    result = float(value)
                except OverflowError as exc:
                    raise CodecError(path, "number exceeds finite float range") from exc
                return result if math.isfinite(result) else fail("non-finite number")
            return value if type(value) is expected else fail(f"{t.name} expected")
        if t.name == "*":
            expected = tuple if encode else list
            if type(value) is not expected or len(value) != len(t.args):
                return fail("tuple of the declared length expected")
            result = [
                convert(a, v, f"[{i}]") for i, (a, v) in enumerate(zip(t.args, value, strict=True))
            ]
            return result if encode else tuple(result)
        if t.name == "list":
            if encode:
                result, seen = [], set()
                while isinstance(value, Variant) and value.tag == "::":
                    if id(value) in seen or type(value.arg) is not tuple or len(value.arg) != 2:
                        return fail("malformed or cyclic list")
                    seen.add(id(value))
                    head, value = value.arg
                    result.append(convert(t.args[0], head, f"[{len(result)}]"))
                if value != NIL:
                    return fail("list must terminate in []")
                return result
            if type(value) is not list:
                return fail("JSON array expected")
            return from_iterable(convert(t.args[0], v, f"[{i}]") for i, v in enumerate(value))
        info = self._info(t)
        if info.kind == "alias" and info.alias is not None:
            return convert(substitute(info.alias, t.args), value, "")
        if info.kind == "record":
            names = [f.name for f in info.fields]
            if encode:
                if not isinstance(value, RecordValue) or value.type_name != info.qname:
                    return fail(f"record {info.qname} expected")
                if [k for k, _ in value.fields] != names:
                    return fail("record fields differ from the declaration")
                fields = dict(value.fields)
            else:
                if type(value) is not dict or set(value) != set(names):
                    return fail("record properties differ from the declaration")
                fields = value
            result = {
                f.name: convert(substitute(f.type, t.args), fields[f.name], f".{f.name}")
                for f in info.fields
            }
            return result if encode else RecordValue(info.qname, tuple(result.items()))
        if encode:
            if not isinstance(value, Variant):
                return fail("variant expected")
            tag = value.tag
            argument = value.arg
            keys = {"tag"} if argument is None else {"tag", "arg"}
        else:
            if type(value) is not dict or not isinstance(value.get("tag"), str):
                return fail("tagged object expected")
            tag = value["tag"]
            argument = value.get("arg")
            keys = set(value)
        ctor = next((c for c in info.ctors if c.name == tag), None)
        if ctor is None:
            return fail(f"unknown constructor {tag!r} of {info.qname}")
        if ctor.arg is None:
            if encode and argument is not None:
                return fail("nullary constructor has an argument")
            if not encode and keys != {"tag"}:
                return fail("nullary constructor requires only tag")
            return {"tag": tag} if encode else Variant(tag, None, ctor.index)
        if not encode and keys != {"tag", "arg"}:
            return fail("constructor requires tag and arg")
        result = convert(substitute(ctor.arg, t.args), argument, ".arg")
        return {"tag": tag, "arg": result} if encode else Variant(tag, result, ctor.index)
