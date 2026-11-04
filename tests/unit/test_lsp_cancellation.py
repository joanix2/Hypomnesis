"""Cancelled editor checks must reap their compiler process."""

import asyncio
from types import SimpleNamespace

import pytest

from hypomnesis.lsp.server import HypomnesisServer


def test_cancelled_check_kills_and_waits_for_worker(tmp_path, monkeypatch):
    async def run():
        started = asyncio.Event()

        class Worker:
            returncode = None
            killed = False
            waited = False

            async def communicate(self, request):
                started.set()
                await asyncio.Event().wait()

            def kill(self):
                self.killed = True
                self.returncode = -9

            async def wait(self):
                self.waited = True

        worker = Worker()

        async def spawn(*args, **kwargs):
            return worker

        monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
        uri = (tmp_path / "p.hyp").as_uri()
        document = SimpleNamespace(version=1, source="let x = 1")
        workspace = SimpleNamespace(
            get_text_document=lambda _: document,
            position_encoding="utf-16",
        )

        class Server(HypomnesisServer):
            @property
            def workspace(self):
                return workspace

        server = Server()
        server.delay = 0
        server.root = tmp_path
        server.open_uris.add(uri)
        task = asyncio.create_task(server.check(uri))
        await asyncio.wait_for(started.wait(), timeout=2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert worker.killed
        assert worker.waited

    asyncio.run(run())
