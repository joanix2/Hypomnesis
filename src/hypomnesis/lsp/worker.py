"""One cancellable static analysis process; stdout is reserved for its JSON response."""

import json
import sys
from pathlib import Path

from lsprotocol.converters import get_converter

from hypomnesis.lsp.analysis import analyze


def main() -> None:
    request = json.load(sys.stdin)
    diagnostics = analyze(
        Path(request["path"]),
        request["source"],
        Path(request["workspace"]),
        request.get("languageRoot"),
        request["overlays"],
        request.get("positionEncoding", "utf-16"),
    )
    print(json.dumps(get_converter().unstructure(diagnostics), ensure_ascii=False))


if __name__ == "__main__":
    main()
