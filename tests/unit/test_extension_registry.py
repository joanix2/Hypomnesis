"""Static manifest indexing, atomic registration and coherent SemVer resolution."""

import json
from typing import ClassVar

import pytest

from hypomnesis.capabilities.protocols import ROLES
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.registry import (
    DependencyCycleError,
    DuplicateManifestError,
    ExtensionRegistry,
    InvalidManifestError,
    MissingDependencyError,
    RegistryError,
    VersionConflictError,
)


def selected(manifests):
    return [(manifest["id"], manifest["version"]) for manifest in manifests]


def test_indexes_all_nine_roles_and_versions(extension_manifest):
    manifests = [
        extension_manifest(f"plugin_{index}", version, role)
        for index, role in enumerate(ROLES)
        for version in ("1.0.0", "2.0.0")
    ]
    registry = ExtensionRegistry(manifests)
    assert registry.ids() == [f"plugin_{index}" for index in range(9)]
    for index, role in enumerate(ROLES):
        identifier = f"plugin_{index}"
        assert registry.ids(role=role) == [identifier]
        assert registry.versions(identifier) == ["2.0.0", "1.0.0"]
        assert selected(registry.list(role=role)) == [
            (identifier, "2.0.0"),
            (identifier, "1.0.0"),
        ]
    assert registry.show("plugin_0")["version"] == "2.0.0"
    assert registry.show("plugin_0", "1.0.0")["version"] == "1.0.0"


def test_role_filter_is_per_version(extension_manifest):
    registry = ExtensionRegistry(
        [extension_manifest(), extension_manifest(version="2.0.0", role="Validator")]
    )
    assert selected(registry.list(role="Solver")) == [("sample", "1.0.0")]


def test_registration_and_inspection_are_isolated(extension_manifest):
    manifest = extension_manifest()
    registry = ExtensionRegistry([manifest])
    manifest["signature"]["input"] = "mutated"
    manifest["dependencies"].append({"id": "absent", "version": "*"})
    for result in (
        registry.show("sample"),
        registry.list()[0],
        registry.resolve({"sample": "*"})[0],
    ):
        assert result["signature"]["input"] == "Json.t"
        result["signature"]["input"] = "also mutated"
        result["dependencies"].append({"id": "absent", "version": "*"})
    assert registry.show("sample")["signature"]["input"] == "Json.t"
    assert registry.show("sample")["dependencies"] == []
    ids, versions = registry.ids(), registry.versions("sample")
    ids.clear()
    versions.clear()
    assert registry.ids() == ["sample"]
    assert registry.versions("sample") == ["1.0.0"]


@pytest.mark.parametrize(
    "changes",
    [
        {"version": "1.0"},
        {"version": "1.0.0-01"},
        {"version": "01.0.0"},
        {"role": "Wizard"},
        {"signature": {"input": "Json.t"}},
        {"input_schema": "not a uri"},
        {"backend": {"kind": "python"}},
        {"permissions": ["invalid permission"]},
        {"error_policy": {"idempotent": False, "timeout_seconds": 1, "max_attempts": 2}},
        {"dependencies": [{"id": "dep", "version": ">=not-a-version"}]},
        {"unexpected": True},
    ],
)
def test_invalid_manifest_is_refused_atomically(changes, extension_manifest):
    registry = ExtensionRegistry([extension_manifest("existing")])
    before = registry.list()
    with pytest.raises(InvalidManifestError):
        registry.add_many([extension_manifest("valid"), extension_manifest(**changes)])
    assert registry.list() == before
    assert registry.ids(role="Solver") == ["existing"]


def test_missing_required_field_is_refused(extension_manifest):
    manifest = extension_manifest()
    del manifest["id"]
    with pytest.raises(InvalidManifestError, match="id"):
        ExtensionRegistry([manifest])


def test_duplicates_are_idempotent_but_conflicts_are_atomic(extension_manifest):
    manifest = extension_manifest()
    registry = ExtensionRegistry([manifest, manifest])
    registry.add(manifest)
    assert len(registry.list()) == 1
    with pytest.raises(DuplicateManifestError, match=r"sample@1\.0\.0"):
        registry.add_many(
            [extension_manifest("new"), extension_manifest(description="different content")]
        )
    assert registry.ids() == ["sample"]
    with pytest.raises(DuplicateManifestError):
        ExtensionRegistry([manifest, extension_manifest(role="Observer")])


def test_uses_supplied_schema_registry(extension_manifest):
    class RecordingSchemas(SchemaRegistry):
        seen: ClassVar[list[str]] = []

        def validate(self, schema_id, instance):
            self.seen.append(schema_id)
            super().validate(schema_id, instance)

    schemas = RecordingSchemas.with_builtin_schemas()
    ExtensionRegistry([extension_manifest()], schemas=schemas)
    assert schemas.seen == ["https://schemas.example.org/hypomnesis/extension-manifest/1.0.0"]


def test_loads_files_and_nonrecursive_directories(extension_manifest, tmp_path):
    directory = tmp_path / "manifests"
    directory.mkdir()
    (directory / "a.json").write_text(json.dumps(extension_manifest("a")))
    (directory / "b.json").write_text(json.dumps(extension_manifest("b")))
    (directory / "ignored.txt").write_text("not JSON")
    nested = directory / "nested"
    nested.mkdir()
    (nested / "ignored.json").write_text("not JSON")
    extra = tmp_path / "c.json"
    extra.write_text(json.dumps(extension_manifest("c")))
    registry = ExtensionRegistry()
    registry.load_paths([directory, extra])
    assert registry.ids() == ["a", "b", "c"]
    registry.load(extra)
    assert len(registry.list()) == 3


@pytest.mark.parametrize("content", ["not JSON", "[]", "null", '{"id": "invalid"}', "\udcff"])
def test_invalid_file_batch_is_atomic(content, extension_manifest, tmp_path):
    good, bad = tmp_path / "a.json", tmp_path / "z.json"
    good.write_text(json.dumps(extension_manifest()))
    bad.write_bytes(content.encode("utf-8", errors="surrogateescape"))
    registry = ExtensionRegistry()
    with pytest.raises(InvalidManifestError):
        registry.load(tmp_path)
    assert registry.list() == []


def test_absent_path_is_explicit_and_atomic(extension_manifest, tmp_path):
    path = tmp_path / "good.json"
    path.write_text(json.dumps(extension_manifest()))
    registry = ExtensionRegistry()
    with pytest.raises(InvalidManifestError, match=r"absent\.json"):
        registry.load_paths([path, tmp_path / "absent.json"])
    assert registry.ids() == []


def test_inspection_does_not_require_dependencies_or_import_backend(
    extension_manifest, trapped_backend, tmp_path
):
    manifest = extension_manifest(dependencies=[("absent", ">=1.0.0,<2")])
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    registry = ExtensionRegistry()
    registry.load(path)
    assert registry.list() == [manifest]
    assert registry.show("sample") == manifest
    with pytest.raises(MissingDependencyError, match="absent"):
        registry.resolve({"sample": "*"})
    registry.add(extension_manifest("absent"))
    assert selected(registry.resolve({"sample": "*"})) == [
        ("absent", "1.0.0"),
        ("sample", "1.0.0"),
    ]
    assert not trapped_backend.exists()


def test_transitive_diamond_is_dependency_first(extension_manifest):
    registry = ExtensionRegistry(
        [
            extension_manifest("root", dependencies=[("left", "*"), ("right", "*")]),
            extension_manifest("left", dependencies=[("shared", ">=1.0.0,<2")]),
            extension_manifest("right", dependencies=[("shared", ">=1.1.0")]),
            extension_manifest("shared", "1.0.0"),
            extension_manifest("shared", "1.5.0"),
            extension_manifest("unused"),
        ]
    )
    assert selected(registry.resolve({"root": "*"})) == [
        ("shared", "1.5.0"),
        ("left", "1.0.0"),
        ("right", "1.0.0"),
        ("root", "1.0.0"),
    ]


def test_backtracking_selects_older_coherent_version(extension_manifest):
    registry = ExtensionRegistry(
        [
            extension_manifest("a", "2.0.0", dependencies=[("shared", ">=2.0.0")]),
            extension_manifest("a", "1.0.0", dependencies=[("shared", "<2")]),
            extension_manifest("z", dependencies=[("shared", "<2")]),
            extension_manifest("shared", "2.0.0"),
            extension_manifest("shared", "1.0.0"),
        ]
    )
    assert selected(registry.resolve({"a": "*", "z": "*"})) == [
        ("shared", "1.0.0"),
        ("a", "1.0.0"),
        ("z", "1.0.0"),
    ]


def test_backtracking_can_avoid_an_absent_dependency(extension_manifest):
    registry = ExtensionRegistry(
        [
            extension_manifest("sample", "2.0.0", dependencies=[("absent", "*")]),
            extension_manifest(),
        ]
    )
    assert selected(registry.resolve({"sample": "*"})) == [("sample", "1.0.0")]


def test_conflicting_shared_constraints_report_origins(extension_manifest):
    registry = ExtensionRegistry(
        [
            extension_manifest("a", dependencies=[("shared", "<2")]),
            extension_manifest("b", dependencies=[("shared", ">=2")]),
            extension_manifest("shared", "1.0.0"),
            extension_manifest("shared", "2.0.0"),
        ]
    )
    before = registry.list()
    with pytest.raises(VersionConflictError) as info:
        registry.resolve({"a": "*", "b": "*"})
    assert "a@1.0.0 requires shared <2" in str(info.value)
    assert "b@1.0.0 requires shared >=2" in str(info.value)
    assert registry.list() == before


def test_absent_root_and_unavailable_version_are_distinct(extension_manifest):
    registry = ExtensionRegistry([extension_manifest()])
    with pytest.raises(MissingDependencyError, match="absent"):
        registry.resolve({"absent": "*"})
    with pytest.raises(VersionConflictError, match="sample >=2"):
        registry.resolve({"sample": ">=2"})
    with pytest.raises(InvalidManifestError, match="constraint"):
        registry.resolve({"sample": "not a constraint"})


@pytest.mark.parametrize("self_cycle", [True, False])
def test_cycles_are_explicit(extension_manifest, self_cycle):
    manifests = [extension_manifest("a", dependencies=[("a" if self_cycle else "b", "*")])]
    if not self_cycle:
        manifests.append(extension_manifest("b", dependencies=[("a", "*")]))
    registry = ExtensionRegistry(manifests)
    with pytest.raises(DependencyCycleError, match="dependency cycle: a ->"):
        registry.resolve({"a": "*"})


def test_semver_ordering_prereleases_and_build_metadata(extension_manifest):
    versions = [
        "1.0.0-preview.custom",
        "1.0.0-preview.custom.2",
        "1.0.0-preview.custom.10",
        "1.0.0",
        "1.0.0+build.one",
        "1.0.0+build.two",
        "2.0.0",
    ]
    registry = ExtensionRegistry([extension_manifest(version=v) for v in reversed(versions)])
    assert registry.versions("sample") == [
        "2.0.0",
        "1.0.0+build.two",
        "1.0.0+build.one",
        "1.0.0",
        "1.0.0-preview.custom.10",
        "1.0.0-preview.custom.2",
        "1.0.0-preview.custom",
    ]
    assert selected(registry.resolve({"sample": "=1.0.0-preview.custom"})) == [
        ("sample", "1.0.0-preview.custom")
    ]
    prerelease = ExtensionRegistry([extension_manifest(version="1.5.0-arbitrary.preview")])
    assert selected(prerelease.resolve({"sample": ">=1.0.0,<2"})) == [
        ("sample", "1.5.0-arbitrary.preview")
    ]


def test_unknown_inspection_inputs_and_empty_registry(extension_manifest):
    registry = ExtensionRegistry([extension_manifest()])
    with pytest.raises(RegistryError, match="unknown role"):
        registry.list(role="Wizard")
    with pytest.raises(MissingDependencyError, match="absent"):
        registry.show("absent")
    with pytest.raises(VersionConflictError, match=r"2\.0\.0"):
        registry.show("sample", "2.0.0")
    assert registry.resolve({}) == []
    assert ExtensionRegistry().list() == []
