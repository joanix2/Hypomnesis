"""Debounced pygls server using isolated, cancellable compiler workers."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from contextlib import suppress
from pathlib import Path

from lsprotocol import types
from lsprotocol.converters import get_converter
from pygls import uris
from pygls.lsp.server import LanguageServer

from hypomnesis import __version__
from hypomnesis.lsp.analysis import diagnostic


def file_path(uri: str) -> Path:
    path = uris.to_fs_path(uri)
    if path is None:
        raise ValueError(f"Not a file URI: {uri}")
    return Path(path).resolve()


class HypomnesisServer(LanguageServer):
    def __init__(self) -> None:
        super().__init__("hypomnesis", __version__)
        self.root = Path.cwd()
        self.language: str | None = None
        self.delay = 0.3
        self.pending: dict[str, asyncio.Task[None]] = {}
        self.open_uris: set[str] = set()

    def configure(self, options: dict) -> None:
        language = options.get("languageRoot", "")
        delay = options.get("debounceMs", 300)
        if not isinstance(language, str) or type(delay) is not int or not 0 <= delay <= 5000:
            self.window_show_message(
                types.ShowMessageParams(
                    type=types.MessageType.Error,
                    message=(
                        "Hypomnesis: languageRoot doit être une chaîne "
                        "et debounceMs un entier 0-5000."
                    ),
                )
            )
            return
        self.language = language or None
        self.delay = delay / 1000

    def schedule(self) -> None:
        for uri in self.open_uris:
            previous = self.pending.pop(uri, None)
            if previous is not None:
                previous.cancel()
            self.pending[uri] = asyncio.create_task(self.check(uri))

    async def check(self, uri: str) -> None:
        process: asyncio.subprocess.Process | None = None
        try:
            await asyncio.sleep(self.delay)
            document = self.workspace.get_text_document(uri)
            version, source = document.version, document.source
            overlays = {
                str(file_path(open_uri)): self.workspace.get_text_document(open_uri).source
                for open_uri in self.open_uris
            }
            request = {
                "path": str(file_path(uri)),
                "source": source,
                "workspace": str(self.root),
                "languageRoot": self.language,
                "overlays": overlays,
                "positionEncoding": self.workspace.position_encoding,
            }
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "hypomnesis.lsp.worker",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(json.dumps(request).encode()), timeout=30
            )
            if process.returncode:
                raise RuntimeError(stderr.decode(errors="replace") or "compiler worker failed")
            diagnostics = get_converter().structure(json.loads(stdout), list[types.Diagnostic])
            if uri in self.open_uris and self.workspace.get_text_document(uri).version == version:
                self.text_document_publish_diagnostics(
                    types.PublishDiagnosticsParams(
                        uri=uri, diagnostics=diagnostics, version=version
                    )
                )
        except (OSError, RuntimeError, TimeoutError, json.JSONDecodeError) as exc:
            message = f"Hypomnesis: analyse impossible : {exc}"
            logging.exception(message)
            self.window_log_message(
                types.LogMessageParams(type=types.MessageType.Error, message=message)
            )
            if uri in self.open_uris:
                self.text_document_publish_diagnostics(
                    types.PublishDiagnosticsParams(
                        uri=uri,
                        diagnostics=[diagnostic(message, "server", None, "")],
                        version=self.workspace.get_text_document(uri).version,
                    )
                )
        finally:
            if process is not None and process.returncode is None:
                process.kill()
                await process.wait()


def create_server() -> HypomnesisServer:
    server = HypomnesisServer()

    @server.feature(types.INITIALIZE)
    def initialize(ls: HypomnesisServer, params: types.InitializeParams) -> None:
        if params.root_uri:
            ls.root = file_path(params.root_uri)
        options = params.initialization_options
        if isinstance(options, dict):
            ls.configure(options)

    @server.feature(types.TEXT_DOCUMENT_DID_OPEN)
    def did_open(ls: HypomnesisServer, params: types.DidOpenTextDocumentParams) -> None:
        if params.text_document.uri.startswith("file:"):
            ls.open_uris.add(params.text_document.uri)
            ls.schedule()

    @server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
    def did_change(ls: HypomnesisServer, params: types.DidChangeTextDocumentParams) -> None:
        ls.schedule()

    @server.feature(types.TEXT_DOCUMENT_DID_SAVE)
    def did_save(ls: HypomnesisServer, params: types.DidSaveTextDocumentParams) -> None:
        ls.schedule()

    @server.feature(types.TEXT_DOCUMENT_DID_CLOSE)
    def did_close(ls: HypomnesisServer, params: types.DidCloseTextDocumentParams) -> None:
        uri = params.text_document.uri
        ls.open_uris.discard(uri)
        pending = ls.pending.pop(uri, None)
        if pending is not None:
            pending.cancel()
        ls.text_document_publish_diagnostics(
            types.PublishDiagnosticsParams(uri=uri, diagnostics=[])
        )
        ls.schedule()

    @server.feature(types.WORKSPACE_DID_CHANGE_CONFIGURATION)
    def configure(ls: HypomnesisServer, params: types.DidChangeConfigurationParams) -> None:
        if isinstance(params.settings, dict):
            options = params.settings.get("hypomnesis", {})
            if isinstance(options, dict):
                ls.configure(options)
                ls.schedule()

    @server.feature(types.SHUTDOWN)
    async def shutdown(ls: HypomnesisServer, params: None) -> None:
        tasks = list(ls.pending.values())
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task

    return server


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    create_server().start_io()


if __name__ == "__main__":
    main()
