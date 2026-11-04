"""Talk JSON-RPC over stdio to the actual pygls server, without VS Code."""

import json
import queue
import subprocess
import sys
import threading

import pytest


class Client:
    def __init__(self, root, encoding=None):
        self.process = subprocess.Popen(
            [sys.executable, "-m", "hypomnesis.lsp.server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.messages = queue.Queue()
        self.thread = threading.Thread(target=self.read, daemon=True)
        self.thread.start()
        self.send(
            "initialize",
            {
                "processId": None,
                "rootUri": root.as_uri(),
                "capabilities": (
                    {"general": {"positionEncodings": [encoding]}} if encoding else {}
                ),
                "initializationOptions": {"debounceMs": 50},
            },
            1,
        )
        response = self.wait(lambda message: message.get("id") == 1)
        assert "error" not in response, response
        assert response["result"]["capabilities"]["textDocumentSync"]["change"] == 2
        self.send("initialized", {})

    def read(self):
        while True:
            headers = {}
            while line := self.process.stdout.readline():
                if line == b"\r\n":
                    break
                key, value = line.decode().split(":", 1)
                headers[key.lower()] = value.strip()
            if not headers:
                return
            message = self.process.stdout.read(int(headers["content-length"]))
            self.messages.put(json.loads(message))

    def send(self, method, params, identifier=None):
        message = {"jsonrpc": "2.0", "method": method, "params": params}
        if identifier is not None:
            message["id"] = identifier
        body = json.dumps(message).encode()
        self.process.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode() + body)
        self.process.stdin.flush()

    def wait(self, predicate):
        while True:
            message = self.messages.get(timeout=15)
            if predicate(message):
                return message

    def diagnostics(self, uri, version):
        return self.wait(
            lambda message: (
                message.get("method") == "textDocument/publishDiagnostics"
                and message["params"]["uri"] == uri
                and message["params"].get("version") == version
            )
        )["params"]["diagnostics"]

    def open(self, uri, text, version=1):
        self.send(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": uri,
                    "languageId": "hypomnesis",
                    "version": version,
                    "text": text,
                }
            },
        )

    def change(self, uri, text, version):
        self.send(
            "textDocument/didChange",
            {"textDocument": {"uri": uri, "version": version}, "contentChanges": [{"text": text}]},
        )

    def close(self):
        try:
            self.send("shutdown", None, 2)
            self.wait(lambda message: message.get("id") == 2)
            self.send("exit", None)
            self.process.wait(timeout=10)
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.wait()
            self.thread.join(timeout=2)
            self.process.stdin.close()
            self.process.stdout.close()
            self.process.stderr.close()


@pytest.fixture
def client(tmp_path):
    client = Client(tmp_path)
    try:
        yield client
    finally:
        client.close()


def test_syntax_type_correction_and_close_over_stdio(client, tmp_path):
    uri = (tmp_path / "p.hyp").as_uri()
    client.open(uri, "let x = (1 +")
    [issue] = client.diagnostics(uri, 1)
    assert issue["code"] == "syntax"
    assert issue["range"]["start"] == {"line": 0, "character": 11}
    client.change(uri, "let x = true + 1", 2)
    [issue] = client.diagnostics(uri, 2)
    assert issue["code"] == "type"
    assert issue["range"] == {
        "start": {"line": 0, "character": 8},
        "end": {"line": 0, "character": 12},
    }
    client.change(uri, "let x = 1 + 1", 3)
    assert client.diagnostics(uri, 3) == []
    client.send("textDocument/didClose", {"textDocument": {"uri": uri}})
    response = client.wait(
        lambda message: (
            message.get("method") == "textDocument/publishDiagnostics"
            and message["params"]["uri"] == uri
        )
    )
    assert response["params"]["diagnostics"] == []


def test_fast_edits_publish_only_the_latest_version(client, tmp_path):
    uri = (tmp_path / "p.hyp").as_uri()
    client.open(uri, "let x = missing")
    for version in range(2, 20):
        client.change(uri, "let x = true + 1", version)
    client.change(uri, "let x = 1", 20)
    message = client.wait(
        lambda message: message.get("method") == "textDocument/publishDiagnostics"
    )
    assert message["params"]["version"] == 20
    assert message["params"]["diagnostics"] == []


def test_incremental_utf16_edit_clears_a_diagnostic(client, tmp_path):
    uri = (tmp_path / "unicode.hyp").as_uri()
    text = 'let x = ("😀", true + 1)'
    client.open(uri, text)
    [issue] = client.diagnostics(uri, 1)
    assert issue["range"]["start"]["character"] == 15
    client.send(
        "textDocument/didChange",
        {
            "textDocument": {"uri": uri, "version": 2},
            "contentChanges": [
                {
                    "range": {
                        "start": {"line": 0, "character": 15},
                        "end": {"line": 0, "character": 19},
                    },
                    "text": "2",
                }
            ],
        },
    )
    assert client.diagnostics(uri, 2) == []


@pytest.mark.parametrize(("encoding", "column"), [("utf-8", 17), ("utf-32", 14)])
def test_negotiated_position_encoding(tmp_path, encoding, column):
    client = Client(tmp_path, encoding)
    try:
        uri = (tmp_path / "p.hyp").as_uri()
        client.open(uri, 'let x = ("😀", true + 1)')
        [issue] = client.diagnostics(uri, 1)
        assert issue["range"]["start"]["character"] == column
    finally:
        client.close()


def test_context_configuration_and_unsaved_m2_dependencies(client, tmp_path):
    root = tmp_path / "language"
    root.mkdir()
    (root / "langage.json").write_text(
        json.dumps(
            {
                "name": "test",
                "version": "0.1.0",
                "description": "Test",
                "sources": ["a.hyp"],
                "procedure": {"kind": "program", "entry": "main"},
            }
        )
    )
    (root / "a.hyp").write_text("let x = 1")
    client.send(
        "workspace/didChangeConfiguration",
        {"settings": {"hypomnesis": {"languageRoot": "language", "debounceMs": 20}}},
    )
    dependency = (root / "a.hyp").as_uri()
    uri = (tmp_path / "program.hyp").as_uri()
    client.open(dependency, "let x = true")
    assert client.diagnostics(dependency, 1) == []
    client.open(uri, "let y = x + 1")
    [issue] = client.diagnostics(uri, 1)
    assert issue["code"] == "type"
    client.change(dependency, "let x = 1", 2)
    assert client.diagnostics(uri, 1) == []
