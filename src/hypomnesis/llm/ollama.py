"""Minimal Ollama client (local HTTP API, standard library only)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_URL = "http://localhost:11434"


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class Reply:
    text: str
    seconds: float
    output_tokens: int
    tokens_per_second: float


class OllamaClient:
    def __init__(self, url: str = DEFAULT_URL, timeout: float = 600.0) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self.url + path,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read())
        except (urllib.error.URLError, TimeoutError) as exc:
            raise LLMError(f"Ollama injoignable ({self.url}) : {exc}") from exc

    def chat(self, model: str, messages: list[dict[str, str]], *, num_ctx: int = 16384) -> Reply:
        if model.startswith("qwen3") and messages and messages[-1]["role"] == "user":
            # Les Qwen3 ignorent parfois `think: false` ; `/no_think` est leur interrupteur.
            messages = [
                *messages[:-1],
                {**messages[-1], "content": messages[-1]["content"] + " /no_think"},
            ]
        start = time.perf_counter()
        data = self._post(
            "/api/chat",
            {
                "model": model,
                "messages": messages,
                "stream": False,
                "think": False,  # traduction directe : pas de raisonnement visible
                "options": {"temperature": 0, "num_ctx": num_ctx},
            },
        )
        if "error" in data:
            raise LLMError(str(data["error"]))
        seconds = time.perf_counter() - start
        tokens = int(data.get("eval_count", 0))
        eval_s = data.get("eval_duration", 0) / 1e9
        return Reply(
            data["message"]["content"], seconds, tokens, tokens / eval_s if eval_s else 0.0
        )

    def models(self) -> list[str]:
        request = urllib.request.Request(self.url + "/api/tags")
        with urllib.request.urlopen(request, timeout=10) as response:
            return [m["name"] for m in json.loads(response.read()).get("models", [])]
