import json

import httpx
import pytest

from app.ai.mock import MockProvider
from app.ai.ollama import OllamaProvider
from app.ai.provider import ProviderResponseError
from app.schemas.learning import GeneratedQuestions


@pytest.mark.anyio
async def test_mock_provider_is_deterministic():
    provider = MockProvider()

    first = await provider.generate_json(dict, "prompt")
    second = await provider.generate_json(dict, "prompt")

    assert first == second == {}
    assert await provider.generate_text("prompt") == "Mock response"
    assert await provider.embed("hello") == [0.0, 0.0, 0.0]


@pytest.mark.anyio
async def test_ollama_provider_uses_httpx_transport():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        return httpx.Response(200, json={"response": "hello"})

    provider = OllamaProvider(base_url="http://ollama.test", transport=httpx.MockTransport(handler))

    assert await provider.generate_text("prompt") == "hello"


async def test_ollama_json_sends_schema_and_returns_an_object():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["format"] == GeneratedQuestions.model_json_schema()
        return httpx.Response(200, json={"response": '{"questions": []}'})

    provider = OllamaProvider(base_url="http://ollama.test", transport=httpx.MockTransport(handler))
    assert await provider.generate_json(GeneratedQuestions, "Return JSON") == {"questions": []}


@pytest.mark.parametrize("content", ["not JSON", "[]"])
async def test_ollama_invalid_json_is_rejected(content):
    provider = OllamaProvider(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"response": content})))
    with pytest.raises(ProviderResponseError):
        await provider.generate_json(dict, "Return JSON")
