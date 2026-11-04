"""Versioned JSON Schema contracts (Draft 2020-12) and their validation.

Schemas are identified by their ``$id``. The registry validates every schema
against the metaschema when it is added, so a broken contract is rejected at
registration time rather than at the first message.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ENVELOPE_ID = "https://schemas.example.org/hypomnesis/envelope/1.0.0"
MANIFEST_ID = "https://schemas.example.org/hypomnesis/extension-manifest/1.0.0"


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


class ContractError(ValueError):
    def __init__(self, schema_id: str, issues: list[ValidationIssue]) -> None:
        super().__init__(f"{schema_id}: " + "; ".join(map(str, issues)))
        self.schema_id = schema_id
        self.issues = issues


class SchemaRegistry:
    def __init__(self, schemas: Iterable[Mapping[str, Any]] = ()) -> None:
        self._schemas: dict[str, Mapping[str, Any]] = {}
        self._registry: Registry = Registry()
        for schema in schemas:
            self.add(schema)

    @classmethod
    def with_builtin_schemas(cls) -> SchemaRegistry:
        directory = files("hypomnesis.contracts").joinpath("schemas")
        schemas = [
            json.loads(entry.read_text(encoding="utf-8"))
            for entry in sorted(directory.iterdir(), key=lambda e: e.name)
            if entry.name.endswith(".json")
        ]
        return cls(schemas)

    def add(self, schema: Mapping[str, Any]) -> str:
        schema = deepcopy(dict(schema))
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id:
            raise ValueError("a contract schema must declare a non-empty $id")
        if schema_id in self._schemas and self._schemas[schema_id] != schema:
            raise ValueError(f"schema {schema_id} is already registered with different content")
        Draft202012Validator.check_schema(schema)
        self._schemas[schema_id] = schema
        resource = Resource.from_contents(schema, default_specification=DRAFT202012)
        self._registry = self._registry.with_resource(schema_id, resource)
        return schema_id

    def __contains__(self, schema_id: str) -> bool:
        return schema_id in self._schemas

    def ids(self) -> list[str]:
        return sorted(self._schemas)

    def schema(self, schema_id: str) -> dict[str, Any]:
        """Inspect a registered contract without exposing mutable registry state."""
        if schema_id not in self._schemas:
            raise ContractError(schema_id, [ValidationIssue("$", "unknown schema")])
        return deepcopy(dict(self._schemas[schema_id]))

    def issues(self, schema_id: str, instance: Any) -> list[ValidationIssue]:
        if schema_id not in self._schemas:
            raise KeyError(f"unknown schema {schema_id}")
        validator = Draft202012Validator(
            self._schemas[schema_id], registry=self._registry, format_checker=FormatChecker()
        )
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
        return [ValidationIssue(e.json_path, e.message) for e in errors]

    def validate(self, schema_id: str, instance: Any) -> None:
        issues = self.issues(schema_id, instance)
        if issues:
            raise ContractError(schema_id, issues)

    def validate_message(self, message: Mapping[str, Any]) -> Any:
        """Validate an envelope, then its payload against the schema it names.

        Returns the payload. The envelope's ``schema_version`` must match the
        version segment that ends the payload schema's ``$id``.
        """
        self.validate(ENVELOPE_ID, message)
        schema_id = message["schema_id"]
        if schema_id not in self:
            raise ContractError(schema_id, [ValidationIssue("$.schema_id", "unknown schema")])
        if schema_id.rstrip("/").rsplit("/", 1)[-1] != message["schema_version"]:
            issue = ValidationIssue("$.schema_version", "does not match the version of schema_id")
            raise ContractError(schema_id, [issue])
        payload = message["payload"]
        self.validate(schema_id, payload)
        return payload
