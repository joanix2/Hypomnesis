import os
import subprocess
import time

import pytest

from hypomnesis.backends.python import BackendError, PythonBackend
from hypomnesis.contracts.registry import SchemaRegistry
from hypomnesis.engine.registry import ExtensionRegistry
from hypomnesis.runtime.natives import default_registry
from hypomnesis.session import Session


def backend(tmp_path, monkeypatch, extension_manifest, body, *, timeout=2, **changes):
    (tmp_path / "test_plugin.py").write_text(body)
    monkeypatch.syspath_prepend(str(tmp_path))
    schema = {"$id": "urn:test:integer", "type": "integer"}
    schemas = SchemaRegistry.with_builtin_schemas()
    schemas.add(schema)
    manifest = extension_manifest()
    manifest.update(
        signature={"input": "int", "output": "int"},
        input_schema=schema["$id"],
        output_schema=schema["$id"],
        backend={"kind": "python", "entry_point": "test_plugin:run"},
        error_policy={"idempotent": False, "max_attempts": 1, "timeout_seconds": timeout},
        **changes,
    )
    registry = ExtensionRegistry([manifest], schemas=schemas)
    return PythonBackend(registry.prepare("sample", Session().checker))


def test_native_call_and_static_analysis(tmp_path, monkeypatch, extension_manifest):
    marker = tmp_path / "imported"
    plugin = backend(
        tmp_path,
        monkeypatch,
        extension_manifest,
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
        "def run(value):\n print('plugin stdout')\n return value + 1\n",
    )
    natives = default_registry()
    plugin.register(natives, "sample.call")
    session = Session(natives)
    session.check('external operation : int -> int = "sample.call"')
    assert not marker.exists()
    session = Session(natives)
    session.load('external operation : int -> int = "sample.call"')
    assert session.eval("operation 41").value == 42
    assert marker.exists()
    assert plugin.tracer.spans


def test_input_rejected_before_import(tmp_path, monkeypatch, extension_manifest):
    marker = tmp_path / "imported"
    plugin = backend(
        tmp_path,
        monkeypatch,
        extension_manifest,
        f"from pathlib import Path\nPath({str(marker)!r}).touch()\ndef run(x): return x",
    )
    with pytest.raises(BackendError, match=r"\[input\]"):
        plugin.invoke(True)
    assert not marker.exists()
    assert any(s.status.is_ok is False for s in plugin.tracer.spans)


@pytest.mark.parametrize(
    ("body", "phase"),
    [
        ("def run(x): return 'wrong'", "output"),
        ("raise RuntimeError('import failed')", "import"),
        ("def run(x): raise ValueError('bad call')", "call"),
        ("import os\ndef run(x): os._exit(7)", "process"),
        ("def run(x): return float('nan')", "output"),
        ("async def run(x): return x", "import"),
    ],
)
def test_failures_are_explicit(tmp_path, monkeypatch, extension_manifest, body, phase):
    plugin = backend(tmp_path, monkeypatch, extension_manifest, body)
    with pytest.raises(BackendError) as error:
        plugin.invoke(1)
    assert error.value.phase == phase
    assert error.value.extension == "sample"


def test_timeout_kills_worker_and_includes_import(tmp_path, monkeypatch, extension_manifest):
    processes = []
    popen = subprocess.Popen

    def start(*args, **kwargs):
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", start)
    pid_file = tmp_path / "pid"
    plugin = backend(
        tmp_path,
        monkeypatch,
        extension_manifest,
        "import os,time\nfrom pathlib import Path\n"
        f"Path({str(pid_file)!r}).write_text(str(os.getpid()))\n"
        "time.sleep(30)\ndef run(x): return x",
        timeout=0.5,
    )
    start = time.monotonic()
    with pytest.raises(BackendError, match="timeout"):
        plugin.invoke(1)
    assert time.monotonic() - start < 3
    assert len(processes) == 1
    assert processes[0].poll() is not None
    with pytest.raises(ProcessLookupError):
        os.kill(processes[0].pid, 0)


def test_permissions_and_preconditions_refused(tmp_path, monkeypatch, extension_manifest):
    with pytest.raises(BackendError, match="permissions"):
        backend(
            tmp_path,
            monkeypatch,
            extension_manifest,
            "def run(x): return x",
            permissions=["device.write"],
        )
    with pytest.raises(BackendError, match="preconditions"):
        backend(
            tmp_path,
            monkeypatch,
            extension_manifest,
            "def run(x): return x",
            preconditions=["must be calibrated"],
        )
