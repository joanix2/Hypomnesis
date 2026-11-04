"""Private JSON worker. Plugin stdout is not the protocol transport."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any


def main() -> None:
    request = json.load(sys.stdin)
    phase = "import"
    response: dict[str, Any]
    try:
        module, name = request["entry_point"].split(":")
        function = importlib.import_module(module)
        for component in name.split("."):
            function = getattr(function, component)
        if not callable(function) or inspect.iscoroutinefunction(function):
            raise TypeError("entry point must be a synchronous callable")
        inspect.signature(function).bind(request["payload"])
        phase = "call"
        result = function(request["payload"])
        phase = "output"
        response = {"ok": True, "value": result}
        encoded = json.dumps(response, allow_nan=False)
    except Exception as exc:
        # This is the external plugin boundary; every failure is sent to the host.
        response = {"ok": False, "phase": phase, "error": f"{type(exc).__name__}: {exc}"}
        encoded = json.dumps(response)
    Path(sys.argv[1]).write_text(encoded)


if __name__ == "__main__":
    main()
