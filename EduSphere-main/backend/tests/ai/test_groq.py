import json

import httpx
import pytest

from app.ai.factory import create_provider
from app.ai.groq import GroqProvider, response_schema
from app.ai.mock import MockProvider
from app.ai.provider import ProviderConfigurationError, ProviderResponseError
from app.core.config import Settings
from app.schemas.activities import ActivityProposal
from app.schemas.learning import GeneratedQuestions


def test_groq_requires_credentials_and_factory_selects_it():
    with pytest.raises(ProviderConfigurationError, match="GROQ_API_KEY"):
        create_provider(Settings(_env_file=None, llm_provider="groq", groq_api_key=None))
    provider = create_provider(Settings(_env_file=None, llm_provider="groq", groq_api_key="test-key"))
    assert isinstance(provider, GroqProvider)
    assert provider.model == "openai/gpt-oss-120b"


async def test_groq_sends_schema_and_authenticated_request():
    def handler(request):
        assert str(request.url) == "https://api.groq.com/openai/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["model"] == "openai/gpt-oss-120b"
        output = payload["response_format"]["json_schema"]
        assert output["strict"] is True
        assert output["schema"]["properties"]["questions"]["maxItems"] == 24
        draft = output["schema"]["$defs"]["QuestionDraft"]
        assert set(draft["required"]) == set(draft["properties"])
        assert draft["additionalProperties"] is False
        assert "default" not in draft["properties"]["term"]
        assert payload["messages"][-1]["content"] == "Return JSON"
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": '{"questions": []}'}}]})

    provider = GroqProvider("test-key", transport=httpx.MockTransport(handler))
    assert await provider.generate_json(GeneratedQuestions, "Return JSON") == {"questions": []}


def test_dynamic_activity_maps_retain_their_schema():
    output = response_schema(ActivityProposal)["json_schema"]
    assert output["strict"] is False
    assert output["schema"]["$defs"]["ActivityBlueprint"]["properties"]["assignments"]["additionalProperties"] == {"type": "string"}


@pytest.mark.parametrize("content,reason", [("[]", "stop"), ("not JSON", "stop"), ('{"questions": []}', "length"), (None, "stop")])
async def test_groq_rejects_invalid_or_truncated_responses(content, reason):
    response = {"choices": [{"finish_reason": reason, "message": {"content": content}}]}
    provider = GroqProvider("test-key", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response)))
    with pytest.raises(ProviderResponseError):
        await provider.generate_json(GeneratedQuestions, "Return JSON")


@pytest.mark.parametrize("status", [401, 429, 500])
async def test_groq_http_errors_do_not_expose_body_or_key(status, monkeypatch):
    async def no_wait(_):
        pass

    monkeypatch.setattr("app.ai.groq.asyncio.sleep", no_wait)
    provider = GroqProvider("test-secret", transport=httpx.MockTransport(lambda _: httpx.Response(status, text="sensitive source")))
    with pytest.raises(ProviderResponseError) as error:
        await provider.generate_text("prompt")
    assert str(status) in str(error.value)
    assert "sensitive" not in str(error.value)
    assert "test-secret" not in str(error.value)


async def test_groq_respects_bounded_rate_limit_retry(monkeypatch):
    delays = []
    calls = []

    async def sleep(delay):
        delays.append(delay)

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, headers={"retry-after": "2.5"})
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]})

    monkeypatch.setattr("app.ai.groq.asyncio.sleep", sleep)
    assert await GroqProvider("test-key", transport=httpx.MockTransport(handler)).generate_text("prompt") == "ok"
    assert delays == [2.5] and len(calls) == 2


async def test_groq_never_fabricates_embeddings():
    with pytest.raises(ProviderConfigurationError, match="embeddings"):
        await GroqProvider("test-key").embed("text")


async def test_groq_delegates_embeddings_to_the_configured_provider():
    provider = GroqProvider("test-key", embedding_provider=MockProvider())
    assert await provider.embed("text") == [0.0, 0.0, 0.0]
