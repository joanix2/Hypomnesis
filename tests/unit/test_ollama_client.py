"""OllamaClient over the official package, against a simulated HTTP server (no network, no GPU)."""

import json
from collections.abc import Callable

import httpx
import pytest

from hypomnesis.llm.ollama import LLMError, OllamaClient

ANSWER = {
    "model": "m",
    "created_at": "2026-01-01T00:00:00Z",
    "message": {"role": "assistant", "content": "let x = 1"},
    "done": True,
    "eval_count": 50,
    "eval_duration": 2_000_000_000,
    "load_duration": 500_000_000,
}


def client_with(
    handler: Callable[[httpx.Request], httpx.Response],
) -> tuple[OllamaClient, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    return OllamaClient("http://fake:1/", transport=httpx.MockTransport(record)), seen


def serving(body: dict) -> Callable[[httpx.Request], httpx.Response]:
    return lambda request: httpx.Response(200, json=body)


def test_chat_sends_the_expected_request_and_measures_the_reply():
    client, seen = client_with(serving(ANSWER))
    messages = [{"role": "user", "content": "hi"}]
    reply = client.chat("llama3", messages, num_ctx=4096)
    request = seen[0]
    assert request.url == "http://fake:1/api/chat"
    body = json.loads(request.content)
    assert body["model"] == "llama3"
    assert body["messages"] == messages
    assert body["stream"] is False
    assert body["think"] is False
    assert body["options"] == {"temperature": 0, "num_ctx": 4096}
    assert "format" not in body
    assert reply.text == "let x = 1"
    assert reply.output_tokens == 50
    assert reply.tokens_per_second == 25.0
    assert reply.load_seconds == 0.5
    assert reply.seconds >= 0


def test_chat_sends_the_sampling_temperature():
    client, seen = client_with(serving(ANSWER))
    client.chat("llama3", [{"role": "user", "content": "hi"}], temperature=0.7)
    assert json.loads(seen[0].content)["options"]["temperature"] == 0.7


def test_zero_duration_gives_zero_throughput():
    client, _ = client_with(serving({**ANSWER, "eval_duration": 0, "eval_count": 0}))
    assert client.chat("m", [{"role": "user", "content": "x"}]).tokens_per_second == 0.0


def test_num_predict_and_format_are_forwarded_when_given():
    client, seen = client_with(serving(ANSWER))
    schema = {"type": "object", "properties": {"a": {"type": "string"}}}
    client.chat("m", [{"role": "user", "content": "x"}], num_predict=64, format=schema)
    body = json.loads(seen[0].content)
    assert body["options"]["num_predict"] == 64
    assert body["format"] == schema


def test_qwen3_gets_no_think_on_the_last_user_message_only():
    client, seen = client_with(serving(ANSWER))
    messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "a"},
        {"role": "user", "content": "last"},
    ]
    client.chat("qwen3:8b", messages)
    sent = json.loads(seen[0].content)["messages"]
    assert [m["content"] for m in sent] == ["s", "first", "a", "last /no_think"]
    assert messages[-1]["content"] == "last"  # the caller's list is untouched


def test_other_models_do_not_get_no_think():
    client, seen = client_with(serving(ANSWER))
    client.chat("llama3", [{"role": "user", "content": "q"}])
    assert json.loads(seen[0].content)["messages"][-1]["content"] == "q"


def test_server_error_becomes_llm_error():
    client, _ = client_with(lambda r: httpx.Response(404, json={"error": "model 'x' not found"}))
    with pytest.raises(LLMError, match="not found"):
        client.chat("x", [{"role": "user", "content": "q"}])


def test_unreachable_server_becomes_llm_error():
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client, _ = client_with(refuse)
    with pytest.raises(LLMError, match=r"Ollama injoignable \(http://fake:1\)"):
        client.chat("m", [{"role": "user", "content": "q"}])
    with pytest.raises(LLMError, match="Ollama injoignable"):
        client.models()


def test_timeout_becomes_llm_error():
    def slow(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    client, _ = client_with(slow)
    with pytest.raises(LLMError, match="Ollama injoignable"):
        client.chat("m", [{"role": "user", "content": "q"}])


def test_models_lists_names():
    client, seen = client_with(serving({"models": [{"model": "a:1"}, {"model": "b:2"}]}))
    assert client.models() == ["a:1", "b:2"]
    assert seen[0].url == "http://fake:1/api/tags"
