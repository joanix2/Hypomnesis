"""Explicit, contract-checked Python extensions executed in a child process."""

from __future__ import annotations

import json
import math
import os
import re
import signal
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import Any

from hypomnesis.contracts.codec import CodecError
from hypomnesis.contracts.registry import ContractError
from hypomnesis.engine.registry import PreparedExtension
from hypomnesis.language.errors import EvaluationError
from hypomnesis.observability.trace import Tracer
from hypomnesis.runtime.natives import NativeRegistry
from hypomnesis.runtime.values import Value

_ENTRY = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")


class BackendError(EvaluationError):
    def __init__(self, extension: str, phase: str, message: str) -> None:
        self.extension = extension
        self.phase = phase
        super().__init__(f"{extension} [{phase}]: {message}")


class PythonBackend:
    """No plugin code is imported until ``invoke`` passes the input contract."""

    def __init__(
        self,
        extension: PreparedExtension,
        *,
        permissions: frozenset[str] = frozenset(),
        tracer: Tracer | None = None,
    ) -> None:
        self.extension = extension
        self.tracer = tracer if tracer is not None else Tracer()
        manifest = extension.manifest
        self.identifier = manifest["id"]
        backend = manifest["backend"]
        self.entry_point = backend["entry_point"]
        self.timeout = manifest["error_policy"]["timeout_seconds"]
        if backend["kind"] != "python" or not _ENTRY.fullmatch(self.entry_point):
            raise BackendError(self.identifier, "prepare", "expected Python module:callable")
        if isinstance(self.timeout, bool) or not math.isfinite(self.timeout) or self.timeout <= 0:
            raise BackendError(self.identifier, "prepare", "timeout must be positive and finite")
        missing = set(manifest["permissions"]) - permissions
        if missing:
            raise BackendError(
                self.identifier, "permissions", f"missing permissions: {', '.join(sorted(missing))}"
            )
        if manifest.get("preconditions"):
            raise BackendError(
                self.identifier, "prepare", "unimplemented declarative preconditions"
            )

    def register(self, registry: NativeRegistry, symbol: str) -> None:
        registry.register(symbol, 1, self.invoke)

    def invoke(self, value: Value) -> Value:
        with self.tracer.span("extension.invoke", extension=self.identifier) as span:
            try:
                with self.tracer.span("extension.input"):
                    payload = self.extension.encode_input(value)
            except (CodecError, ContractError) as exc:
                raise BackendError(self.identifier, "input", str(exc)) from exc
            response = self._call(payload)
            try:
                with self.tracer.span("extension.output"):
                    result = self.extension.decode_output(response)
            except (CodecError, ContractError) as exc:
                raise BackendError(self.identifier, "output", str(exc)) from exc
            span.set_attribute("result", "success")
            return result

    def _call(self, payload: Any) -> Any:
        request = json.dumps({"entry_point": self.entry_point, "payload": payload}, allow_nan=False)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(str(Path(p or ".").resolve()) for p in sys.path)
        with tempfile.TemporaryDirectory(prefix="hyp-python-") as directory:
            response_path = Path(directory) / "response.json"
            with tempfile.TemporaryFile() as errors, self.tracer.span("extension.process"):
                try:
                    process = subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "hypomnesis.backends.python.worker",
                            str(response_path),
                        ],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.DEVNULL,
                        stderr=errors,
                        env=env,
                        start_new_session=True,
                    )
                except OSError as exc:
                    raise BackendError(self.identifier, "start", str(exc)) from exc
                try:
                    try:
                        process.communicate(request.encode(), timeout=self.timeout)
                    except subprocess.TimeoutExpired as exc:
                        raise BackendError(
                            self.identifier, "timeout", f"exceeded {self.timeout}s"
                        ) from exc
                finally:
                    # Plugins may have spawned children, including after their own exit.
                    with suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                if process.returncode:
                    errors.seek(0)
                    detail = errors.read(4096).decode(errors="replace")
                    raise BackendError(
                        self.identifier, "process", f"exit {process.returncode}: {detail}"
                    )
                try:
                    response = json.loads(response_path.read_text())
                except (OSError, ValueError) as exc:
                    raise BackendError(self.identifier, "protocol", str(exc)) from exc
                if not isinstance(response, dict):
                    raise BackendError(self.identifier, "protocol", "invalid worker response")
                if response.get("ok") is False:
                    if (
                        set(response) != {"ok", "error", "phase"}
                        or not isinstance(response["phase"], str)
                        or not isinstance(response["error"], str)
                    ):
                        raise BackendError(self.identifier, "protocol", "invalid worker error")
                    raise BackendError(self.identifier, response["phase"], response["error"])
                if response.get("ok") is not True or set(response) != {"ok", "value"}:
                    raise BackendError(self.identifier, "protocol", "invalid worker status")
                return response["value"]
