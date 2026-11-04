"""Static extension manifests: inspection and dependency resolution, never backend loading."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
from resolvelib import BaseReporter, Resolver
from resolvelib.providers import AbstractProvider
from resolvelib.resolvers import ResolutionImpossible, ResolutionTooDeep
from semantic_version import SimpleSpec, Version

from hypomnesis.capabilities.protocols import ROLES
from hypomnesis.contracts.registry import MANIFEST_ID, ContractError, SchemaRegistry


class RegistryError(ValueError):
    """A manifest cannot be registered, inspected or resolved."""


class InvalidManifestError(RegistryError):
    """A manifest violates its schema or its version constraints."""


class DuplicateManifestError(RegistryError):
    """An id/version pair already has different metadata."""


class MissingDependencyError(RegistryError):
    """A required extension id is absent."""


class VersionConflictError(RegistryError):
    """No coherent selection satisfies all version constraints."""


class DependencyCycleError(RegistryError):
    """The selected dependency graph contains a cycle."""


@dataclass(frozen=True)
class _Requirement:
    id: str
    constraint: str

    def __post_init__(self) -> None:
        try:
            SimpleSpec(self.constraint)
        except ValueError as exc:
            raise InvalidManifestError(
                f"invalid version constraint for {self.id}: {self.constraint!r}"
            ) from exc


@dataclass(frozen=True)
class _Candidate:
    id: str
    version: str


class _Provider(AbstractProvider[_Requirement, _Candidate, str]):
    def __init__(self, manifests: dict[str, dict[str, dict[str, Any]]]) -> None:
        self.manifests = manifests

    def identify(self, requirement_or_candidate: _Requirement | _Candidate) -> str:
        return requirement_or_candidate.id

    def get_preference(
        self,
        identifier: str,
        resolutions: Any,
        candidates: Any,
        information: Any,
        backtrack_causes: Any,
    ) -> str:
        return identifier

    def find_matches(
        self,
        identifier: str,
        requirements: Mapping[str, Iterator[_Requirement]],
        incompatibilities: Mapping[str, Iterator[_Candidate]],
    ) -> list[_Candidate]:
        required = list(requirements[identifier])
        excluded = set(incompatibilities[identifier])
        versions = sorted(
            self.manifests.get(identifier, {}),
            key=lambda v: (Version(v).truncate("prerelease"), v),
            reverse=True,
        )
        return [
            candidate
            for version in versions
            if (candidate := _Candidate(identifier, version)) not in excluded
            and all(self.is_satisfied_by(requirement, candidate) for requirement in required)
        ]

    def is_satisfied_by(self, requirement: _Requirement, candidate: _Candidate) -> bool:
        return requirement.id == candidate.id and SimpleSpec(requirement.constraint).match(
            Version(candidate.version)
        )

    def get_dependencies(self, candidate: _Candidate) -> list[_Requirement]:
        manifest = self.manifests[candidate.id][candidate.version]
        return [_Requirement(d["id"], d["version"]) for d in manifest.get("dependencies", [])]


class ExtensionRegistry:
    """Own copies of validated metadata, indexed by id, role and exact SemVer string.

    Registration does not require installed dependencies. ``resolve`` selects one version
    per id, prefers newer versions and returns copies in dependency-first order.
    """

    def __init__(
        self,
        manifests: Iterable[Mapping[str, Any]] = (),
        *,
        schemas: SchemaRegistry | None = None,
    ) -> None:
        self._schemas = schemas if schemas is not None else SchemaRegistry.with_builtin_schemas()
        self._by_id: dict[str, dict[str, dict[str, Any]]] = {}
        self._by_role: dict[str, set[tuple[str, str]]] = {role: set() for role in ROLES}
        self.add_many(manifests)

    def add(self, manifest: Mapping[str, Any]) -> None:
        """Register a manifest; identical duplicates are idempotent."""
        self.add_many([manifest])

    def add_many(self, manifests: Iterable[Mapping[str, Any]]) -> None:
        """Validate an entire batch before changing any index."""
        pending: dict[tuple[str, str], dict[str, Any]] = {}
        for manifest in manifests:
            owned = deepcopy(dict(manifest))
            try:
                self._schemas.validate(MANIFEST_ID, owned)
                Version(owned["version"])
                for dependency in owned.get("dependencies", []):
                    _Requirement(dependency["id"], dependency["version"])
            except (ContractError, ValueError) as exc:
                raise InvalidManifestError(f"invalid manifest: {exc}") from exc
            key = owned["id"], owned["version"]
            previous = pending.get(key, self._by_id.get(key[0], {}).get(key[1]))
            if previous is not None and previous != owned:
                raise DuplicateManifestError(
                    f"manifest {key[0]}@{key[1]} is already registered with different content"
                )
            pending[key] = owned
        for (identifier, version), manifest in pending.items():
            self._by_id.setdefault(identifier, {})[version] = manifest
            self._by_role[manifest["role"]].add((identifier, version))

    def load(self, path: str | Path) -> None:
        """Load a JSON file or a directory's immediate *.json files, atomically."""
        self.load_paths([path])

    def load_paths(self, paths: Iterable[str | Path]) -> None:
        """Read all explicit paths before registering anything; never import a backend."""
        manifests = []
        for item in paths:
            path = Path(item)
            try:
                entries = sorted(path.glob("*.json")) if path.is_dir() else [path]
                for entry in entries:
                    manifest = json.loads(entry.read_text(encoding="utf-8"))
                    if not isinstance(manifest, dict):
                        raise InvalidManifestError(f"{entry}: manifest must be a JSON object")
                    manifests.append(manifest)
            except (OSError, ValueError) as exc:
                raise InvalidManifestError(f"{path}: {exc}") from exc
        self.add_many(manifests)

    def ids(self, *, role: str | None = None) -> list[str]:
        """List ids alphabetically, optionally restricted to one of the nine roles."""
        if role is None:
            return sorted(self._by_id)
        if role not in ROLES:
            raise RegistryError(f"unknown role {role!r}; expected one of {', '.join(ROLES)}")
        return sorted({identifier for identifier, _ in self._by_role[role]})

    def versions(self, identifier: str) -> list[str]:
        """List exact version strings, newest SemVer first (text breaks build-metadata ties)."""
        if identifier not in self._by_id:
            raise MissingDependencyError(f"extension {identifier!r} is absent")
        return sorted(
            self._by_id[identifier],
            key=lambda v: (Version(v).truncate("prerelease"), v),
            reverse=True,
        )

    def list(self, *, role: str | None = None) -> list[dict[str, Any]]:
        """Inspect all registered versions without resolving their dependencies."""
        return [
            self.show(identifier, version)
            for identifier in self.ids(role=role)
            for version in self.versions(identifier)
            if role is None or (identifier, version) in self._by_role[role]
        ]

    def show(self, identifier: str, version: str | None = None) -> dict[str, Any]:
        """Inspect an exact version, or the latest when omitted; return a deep copy."""
        versions = self.versions(identifier)
        if version is None:
            version = versions[0]
        if version not in self._by_id[identifier]:
            raise VersionConflictError(f"extension {identifier!r} has no version {version!r}")
        return deepcopy(self._by_id[identifier][version])

    def resolve(self, requirements: Mapping[str, str]) -> list[dict[str, Any]]:
        """Resolve root id -> SimpleSpec constraints and all transitive dependencies.

        Inspection is independent of this operation. Cycles in the selected graph are
        refused, even though resolvelib itself permits cyclic package dependencies.
        """
        provider = _Provider(self._by_id)
        resolver = Resolver(provider, BaseReporter())
        try:
            result = resolver.resolve(
                [
                    _Requirement(identifier, constraint)
                    for identifier, constraint in requirements.items()
                ],
                max_rounds=10000,
            )
        except ResolutionImpossible as exc:
            details = []
            missing = False
            for cause in exc.causes:
                requirement, parent = cause.requirement, cause.parent
                absent = requirement.id not in self._by_id
                missing |= absent
                origin = f"{parent.id}@{parent.version}" if parent else "root"
                details.append(
                    f"{origin} requires {requirement.id} {requirement.constraint}"
                    + (" (absent)" if absent else "")
                )
            error = MissingDependencyError if missing else VersionConflictError
            raise error("dependency resolution failed: " + "; ".join(details)) from exc
        except ResolutionTooDeep as exc:
            raise RegistryError("dependency resolution exceeded 10000 rounds") from exc
        graph = nx.DiGraph()
        for identifier, candidate in result.mapping.items():
            graph.add_node(identifier)
            for dependency in provider.get_dependencies(candidate):
                graph.add_edge(dependency.id, identifier)
        if not nx.is_directed_acyclic_graph(graph):
            cycle = nx.find_cycle(graph)
            path = " -> ".join([cycle[0][0], *(target for _, target in cycle)])
            raise DependencyCycleError(f"dependency cycle: {path}")
        return [
            self.show(identifier, result.mapping[identifier].version)
            for identifier in nx.lexicographical_topological_sort(graph)
        ]
