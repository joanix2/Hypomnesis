"""Ollama client: thin layer over the official `ollama` package.

The client is imported lazily; importing the package does not contact a server.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import httpx

DEFAULT_URL = "http://localhost:11434"


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class Reply:
    text: str
    seconds: float
    output_tokens: int
    tokens_per_second: float
    load_seconds: float = 0.0  # model load time reported by the server (part of `seconds`)


class OllamaClient:
    def __init__(
        self,
        url: str = DEFAULT_URL,
        timeout: float = 600.0,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        import ollama

        self.url = url.rstrip("/")
        self.timeout = timeout
        # `transport` is forwarded to httpx: tests inject a simulated server through it.
        self._client = ollama.Client(host=self.url, timeout=timeout, transport=transport)

    def _unreachable(self, exc: Exception) -> LLMError:
        return LLMError(f"Ollama injoignable ({self.url}) : {exc}")

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        num_ctx: int = 16384,
        num_predict: int | None = None,
        format: dict[str, Any] | None = None,
        temperature: float = 0.0,
    ) -> Reply:
        """One non-streaming chat turn; `format` is an optional JSON Schema (structured output).

        At temperature 0 (default) answers are deterministic; repeated trials need ``> 0``."""
        import httpx
        import ollama

        if model.startswith("qwen3") and messages and messages[-1]["role"] == "user":
            # Les Qwen3 ignorent parfois `think: false` ; `/no_think` est leur interrupteur.
            messages = [
                *messages[:-1],
                {**messages[-1], "content": messages[-1]["content"] + " /no_think"},
            ]
        options: dict[str, Any] = {"temperature": temperature, "num_ctx": num_ctx}
        if num_predict is not None:
            options["num_predict"] = num_predict
        start = time.perf_counter()
        try:
            response = self._client.chat(
                model=model,
                messages=messages,
                stream=False,
                think=False,  # traduction directe : pas de raisonnement visible
                format=format,
                options=options,
            )
        except ollama.ResponseError as exc:
            raise LLMError(str(exc.error)) from exc
        except (ConnectionError, httpx.HTTPError) as exc:
            raise self._unreachable(exc) from exc
        seconds = time.perf_counter() - start
        tokens = response.eval_count or 0
        eval_s = (response.eval_duration or 0) / 1e9
        return Reply(
            response.message.content or "",
            seconds,
            tokens,
            tokens / eval_s if eval_s else 0.0,
            (response.load_duration or 0) / 1e9,
        )

    def models(self) -> list[str]:
        import httpx
        import ollama

        try:
            listing = self._client.list()
        except ollama.ResponseError as exc:
            raise LLMError(str(exc.error)) from exc
        except (ConnectionError, httpx.HTTPError) as exc:
            raise self._unreachable(exc) from exc
        return [m.model for m in listing.models if m.model]
