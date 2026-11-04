"""Fixtures for static extension metadata and backend non-execution checks."""

import sys

import pytest


@pytest.fixture
def extension_manifest():
    def make(identifier="sample", version="1.0.0", role="Solver", dependencies=(), **changes):
        manifest = {
            "id": identifier,
            "version": version,
            "role": role,
            "signature": {"input": "Json.t", "output": "Json.t"},
            "input_schema": "https://schemas.example.org/input/1.0.0",
            "output_schema": "https://schemas.example.org/output/1.0.0",
            "permissions": [],
            "backend": {"kind": "python", "entry_point": "hyp041_trapped_backend:plugin"},
            "error_policy": {"idempotent": True, "timeout_seconds": 1, "max_attempts": 1},
            "dependencies": [{"id": name, "version": spec} for name, spec in dependencies],
        }
        return {**manifest, **changes}

    return make


@pytest.fixture
def trapped_backend(tmp_path, monkeypatch):
    marker = tmp_path / "backend_was_imported"
    backend = tmp_path / "hyp041_trapped_backend.py"
    backend.write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
        "raise RuntimeError('backend must never be imported')\n",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    assert "hyp041_trapped_backend" not in sys.modules
    yield marker
    assert not marker.exists()
    assert "hyp041_trapped_backend" not in sys.modules
