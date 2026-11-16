from types import SimpleNamespace

import pytest
from google import genai
from google.genai.errors import ServerError
from google.genai.types import HttpOptions
from httpx import MockTransport, Request, Response

from app.ai.google_genai import GeminiProvider, VertexProvider
from app.ai.provider import ProviderConfigurationError, ProviderResponseError
from app.core.config import Settings
from app.schemas.activities import ActivityProposal


class FakeModels:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        config = kwargs["config"]
        if getattr(config, "response_mime_type", None) == "application/json":
            return SimpleNamespace(text='{"answer":"ok"}')
        return SimpleNamespace(text="hello")

    async def embed_content(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(embeddings=[SimpleNamespace(values=[1, 2.5])])


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()
        self.aio = SimpleNamespace(models=self.models)


@pytest.mark.anyio
async def test_gemini_adapter_covers_text_json_and_embeddings() -> None:
    fake = FakeClient()
    settings = Settings(_env_file=None, gemini_api_key="placeholder", gemini_text_model="text-v", gemini_json_model="json-v")
    provider = GeminiProvider(settings, client_factory=lambda **_: fake)

    assert await provider.generate_text("prompt") == "hello"
    assert await provider.generate_json(dict, "prompt") == {"answer": "ok"}
    assert await provider.embed("text") == [1.0, 2.5]
    assert fake.models.calls[0]["model"] == "text-v"
    assert fake.models.calls[1]["model"] == "json-v"


def test_vertex_adapter_passes_project_and_location_without_reading_credentials() -> None:
    fake = FakeClient()
    captured: dict[str, object] = {}

    def factory(**kwargs: object) -> FakeClient:
        captured.update(kwargs)
        return fake

    VertexProvider(Settings(_env_file=None, vertex_project="project-v", vertex_location="europe-west4"), client_factory=factory)

    assert captured == {"vertexai": True, "project": "project-v", "location": "europe-west4"}


def test_missing_provider_credentials_are_safe() -> None:
    with pytest.raises(ProviderConfigurationError, match="not configured"):
        GeminiProvider(Settings(_env_file=None))
    with pytest.raises(ProviderConfigurationError, match="not configured"):
        VertexProvider(Settings(_env_file=None))


@pytest.mark.anyio
async def test_invalid_json_is_rejected() -> None:
    fake = FakeClient()

    async def invalid(**_: object) -> SimpleNamespace:
        return SimpleNamespace(text="not-json")

    fake.models.generate_content = invalid  # type: ignore[method-assign]
    provider = GeminiProvider(Settings(_env_file=None, gemini_api_key="placeholder"), client_factory=lambda **_: fake)

    with pytest.raises(ProviderResponseError, match="invalid JSON"):
        await provider.generate_json(dict, "prompt")


@pytest.mark.anyio
async def test_transient_generation_errors_are_retried() -> None:
    fake = FakeClient()
    attempts = 0

    async def flaky(**_: object) -> SimpleNamespace:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ServerError(503, {"error": {"message": "temporarily busy"}})
        return SimpleNamespace(text='{"answer":"ok"}')

    fake.models.generate_content = flaky  # type: ignore[method-assign]
    provider = GeminiProvider(Settings(_env_file=None, gemini_api_key="placeholder"), client_factory=lambda **_: fake)

    assert await provider.generate_json(dict, "prompt") == {"answer": "ok"}
    assert attempts == 3


@pytest.mark.anyio
async def test_game_schema_serializes_maps_and_tuple_links_without_a_network_call() -> None:
    import json

    captured = []

    def handle(request: Request) -> Response:
        captured.append(json.loads(request.content))
        return Response(200, json={"candidates": [{"content": {"role": "model", "parts": [{"text": '{"activity":null}'}]}}]})

    def factory(**kwargs: object):
        return genai.Client(**kwargs, http_options=HttpOptions(async_client_args={"transport": MockTransport(handle)}))

    provider = GeminiProvider(Settings(_env_file=None, gemini_api_key="local-test-placeholder"), client_factory=factory)
    assert await provider.generate_json(ActivityProposal, "Design a source-grounded game") == {"activity": None}
    wire_schema = captured[0]["generationConfig"]["responseJsonSchema"]
    assert wire_schema == ActivityProposal.model_json_schema()
