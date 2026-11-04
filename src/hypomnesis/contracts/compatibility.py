"""Conservative, directional inclusion for the structural subset in ADR 0010."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, NoReturn
from urllib.parse import unquote, urlsplit

from jsonschema import Draft202012Validator

from hypomnesis.contracts.registry import SchemaRegistry


class CompatibilityError(ValueError):
    pass


class UnsupportedSchemaError(CompatibilityError):
    pass


_ANNOTATIONS = {
    "$schema",
    "$id",
    "$defs",
    "title",
    "description",
    "default",
    "examples",
    "$comment",
    "deprecated",
    "readOnly",
    "writeOnly",
}
_KEYWORDS = {
    "$ref",
    "type",
    "const",
    "enum",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "prefixItems",
    "minItems",
    "maxItems",
    "minLength",
    "maxLength",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "anyOf",
    "oneOf",
}


class _Inclusion:
    def __init__(self, registry: SchemaRegistry) -> None:
        self.registry = registry
        self.documents: dict[str, dict[str, Any]] = {}
        self.checked: set[tuple[int, int]] = set()
        self.pairs: set[tuple[int, int, int, int]] = set()

    def dereference(self, node: Any, root: Any) -> tuple[Any, Any]:
        seen = set()
        while isinstance(node, dict):
            if node is not root and "$id" in node:
                raise UnsupportedSchemaError("nested resource identifiers are unsupported")
            if (
                "$schema" in node
                and node["$schema"] != "https://json-schema.org/draft/2020-12/schema"
            ):
                raise UnsupportedSchemaError("only JSON Schema Draft 2020-12 is supported")
            if "$ref" not in node:
                break
            if (id(node), id(root)) in seen:
                raise UnsupportedSchemaError("unproductive reference cycle")
            seen.add((id(node), id(root)))
            if set(node) - _ANNOTATIONS - {"$ref"}:
                raise UnsupportedSchemaError("$ref with validation siblings is unsupported")
            uri, _, fragment = node["$ref"].partition("#")
            if uri:
                if not urlsplit(uri).scheme:
                    raise UnsupportedSchemaError("relative document references are unsupported")
                if uri not in self.documents:
                    self.documents[uri] = self.registry.schema(uri)
                root = self.documents[uri]
            node = root
            if fragment:
                if not fragment.startswith("/"):
                    raise UnsupportedSchemaError("only JSON Pointer references are supported")
                try:
                    for segment in unquote(fragment[1:]).split("/"):
                        key = segment.replace("~1", "/").replace("~0", "~")
                        if isinstance(node, list):
                            if not key.isdecimal() or (key != "0" and key.startswith("0")):
                                raise ValueError("invalid array index in JSON Pointer")
                            node = node[int(key)]
                        else:
                            node = node[key]
                except (KeyError, IndexError, ValueError, TypeError) as exc:
                    raise CompatibilityError(f"unresolved reference #{fragment}") from exc
        if not isinstance(node, dict | bool):
            raise CompatibilityError("reference target is not a JSON Schema")
        return node, root

    def check(self, node: Any, root: Any) -> None:
        node, root = self.dereference(node, root)
        key = id(node), id(root)
        if key in self.checked or isinstance(node, bool):
            return
        self.checked.add(key)
        unknown = set(node) - _KEYWORDS - _ANNOTATIONS
        if unknown:
            raise UnsupportedSchemaError(
                f"unsupported schema keywords: {', '.join(sorted(unknown))}"
            )
        if isinstance(node.get("type"), list):
            raise UnsupportedSchemaError("type arrays are unsupported; use anyOf")
        if "anyOf" in node or "oneOf" in node:
            keyword = "anyOf" if "anyOf" in node else "oneOf"
            if set(node) - _ANNOTATIONS - {keyword}:
                raise UnsupportedSchemaError("union with validation siblings is unsupported")
            branches = node[keyword]
            if keyword == "oneOf":
                tags = []
                for branch in branches:
                    branch, _ = self.dereference(branch, root)
                    if not isinstance(branch, dict) or branch.get("type") != "object":
                        raise UnsupportedSchemaError("oneOf requires disjoint tagged objects")
                    tag = branch.get("properties", {}).get("tag", {})
                    if "tag" not in branch.get("required", []) or not isinstance(
                        tag.get("const"), str
                    ):
                        raise UnsupportedSchemaError("oneOf requires a required constant tag")
                    tags.append(tag["const"])
                if len(set(tags)) != len(tags):
                    raise UnsupportedSchemaError("oneOf tags must be distinct")
            for branch in branches:
                self.check(branch, root)
        for child in node.get("properties", {}).values():
            self.check(child, root)
        for child in node.get("prefixItems", []):
            self.check(child, root)
        for name in ("items", "additionalProperties"):
            if name in node:
                self.check(node[name], root)
        if node.get("type") == "object" and node.get("additionalProperties", True) is not False:
            raise UnsupportedSchemaError("only closed objects are statically verifiable")
        if "properties" in node and node.get("type") != "object":
            raise UnsupportedSchemaError("properties requires type object")
        if any(k in node for k in ("items", "prefixItems")) and node.get("type") != "array":
            raise UnsupportedSchemaError("items requires type array")
        if node.get("type") not in (
            None,
            "null",
            "boolean",
            "integer",
            "number",
            "string",
            "array",
            "object",
        ):
            raise UnsupportedSchemaError("unknown JSON type")

    def accepts(self, node: Any, root: Any, value: Any) -> bool:
        node, root = self.dereference(node, root)
        if isinstance(node, bool):
            return node
        for union in ("anyOf", "oneOf"):
            if union in node:
                hits = sum(self.accepts(branch, root, value) for branch in node[union])
                return hits > 0 if union == "anyOf" else hits == 1
        scalar = {
            k: v
            for k, v in node.items()
            if k
            not in _ANNOTATIONS | {"properties", "items", "prefixItems", "additionalProperties"}
        }
        if not Draft202012Validator(scalar).is_valid(value):
            return False
        if isinstance(value, dict):
            properties = node.get("properties", {})
            return all(
                self.accepts(properties.get(k, node.get("additionalProperties", True)), root, v)
                for k, v in value.items()
            )
        if isinstance(value, list):
            prefix = node.get("prefixItems", [])
            return all(
                self.accepts(prefix[i] if i < len(prefix) else node.get("items", True), root, v)
                for i, v in enumerate(value)
            )
        return True

    def includes(self, source: Any, sr: Any, target: Any, tr: Any, path: str = "$") -> None:
        source, sr = self.dereference(source, sr)
        target, tr = self.dereference(target, tr)
        pair = id(source), id(sr), id(target), id(tr)
        if pair in self.pairs:
            return
        self.pairs.add(pair)

        def refuse(message: str) -> NoReturn:
            raise CompatibilityError(f"{path}: {message}")

        if source is False or target is True:
            return
        if isinstance(target, dict) and not set(target) - _ANNOTATIONS:
            return
        if target is False or source is True:
            refuse("schema inclusion cannot be established")
        sb = source.get("anyOf", source.get("oneOf"))
        tb = target.get("anyOf", target.get("oneOf"))
        if sb is not None:
            for branch in sb:
                self.includes(branch, sr, target, tr, path)
            return
        if tb is not None:
            saved = set(self.pairs)
            for branch in tb:
                try:
                    self.includes(source, sr, branch, tr, path)
                    return
                except CompatibilityError:
                    self.pairs = set(saved)
            refuse("no target union branch covers the source")
        finite = [source["const"]] if "const" in source else source.get("enum")
        if finite is not None:
            if any(not self.accepts(target, tr, v) for v in finite):
                refuse("source constants are not accepted by target")
            return
        if "const" in target or "enum" in target:
            refuse("unrestricted source is not included in finite target")
        st, tt = source.get("type"), target.get("type")
        if st != tt and not (st == "integer" and tt == "number"):
            refuse(f"type {st!r} is not included in {tt!r}")
        if st is None:
            if set(target) - _ANNOTATIONS:
                refuse("untyped schema inclusion is not established")
            return
        if st in ("integer", "number"):
            for low, ordinary, exclusive in (
                (True, "minimum", "exclusiveMinimum"),
                (False, "maximum", "exclusiveMaximum"),
            ):
                bounds = [(target[k], k == exclusive) for k in (ordinary, exclusive) if k in target]
                available = [
                    (source[k], k == exclusive) for k in (ordinary, exclusive) if k in source
                ]
                for bound, strict in bounds:
                    if not any(
                        (v > bound if low else v < bound) or (v == bound and (s or not strict))
                        for v, s in available
                    ):
                        refuse(f"source does not imply {ordinary} {bound}")
        if st in ("string", "array"):
            minimum, maximum = (
                ("minLength", "maxLength") if st == "string" else ("minItems", "maxItems")
            )
            if source.get(minimum, 0) < target.get(minimum, 0):
                refuse(f"source does not imply {minimum}")
            if maximum in target and source.get(maximum, float("inf")) > target[maximum]:
                refuse(f"source does not imply {maximum}")
        if st == "object":
            sp, tp = source.get("properties", {}), target.get("properties", {})
            if not set(target.get("required", [])) <= set(source.get("required", [])):
                refuse("target required properties are not guaranteed")
            if not set(sp) <= set(tp):
                refuse("source permits properties forbidden by target")
            for name in sp:
                self.includes(sp[name], sr, tp[name], tr, path + "." + name)
        if st == "array":
            sp, tp = source.get("prefixItems", []), target.get("prefixItems", [])
            limit = source.get("maxItems", float("inf"))
            for index in range(max(len(sp), len(tp))):
                if index >= limit:
                    break
                s = sp[index] if index < len(sp) else source.get("items", True)
                t = tp[index] if index < len(tp) else target.get("items", True)
                self.includes(s, sr, t, tr, f"{path}[{index}]")
            if limit > max(len(sp), len(tp)):
                self.includes(
                    source.get("items", True), sr, target.get("items", True), tr, path + "[*]"
                )


def require_inclusion(
    source: Mapping[str, Any], target: Mapping[str, Any], registry: SchemaRegistry
) -> None:
    """Prove source ⊆ target for the supported structural subset, or refuse explicitly."""
    Draft202012Validator.check_schema(source)
    Draft202012Validator.check_schema(target)
    checker = _Inclusion(registry)
    checker.check(source, source)
    checker.check(target, target)
    checker.includes(source, source, target, target)
