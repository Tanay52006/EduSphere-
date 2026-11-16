import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import TypeAdapter

from app.ai.provider import ProviderConfigurationError, ProviderResponseError
from app.core.config import Settings

ClientFactory = Callable[..., Any]
_TRANSIENT_PROVIDER_CODES = {429, 500, 502, 503, 504}
_RETRY_DELAYS_SECONDS = (0.5, 1.0)


async def _with_transient_retry(operation: Callable[[], Awaitable[Any]]) -> Any:
    for _attempt, delay in enumerate((*_RETRY_DELAYS_SECONDS, None)):
        try:
            return await operation()
        except genai_errors.APIError as exc:
            if exc.code not in _TRANSIENT_PROVIDER_CODES or delay is None:
                raise
            await asyncio.sleep(delay)
    raise AssertionError("retry loop did not return or raise")


class _GoogleGenAIProvider:
    def __init__(self, client: Any, text_model: str, json_model: str, embedding_model: str) -> None:
        self.client = client
        self.text_model = text_model
        self.json_model = json_model
        self.embedding_model = embedding_model

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        response = await _with_transient_retry(
            lambda: self.client.aio.models.generate_content(
                model=self.text_model,
                contents=prompt,
                config=types.GenerateContentConfig(**kwargs) if kwargs else None,
            )
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str):
            raise ProviderResponseError("provider returned no text")
        return text

    async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> dict[str, Any]:
        # JSON Schema retains map/tuple constraints that the older OpenAPI subset rejects.
        json_schema = schema.model_json_schema() if hasattr(schema, "model_json_schema") else TypeAdapter(schema).json_schema()
        config = {"response_mime_type": "application/json", "response_json_schema": json_schema, **kwargs}
        response = await _with_transient_retry(
            lambda: self.client.aio.models.generate_content(
                model=self.json_model,
                contents=prompt,
                config=types.GenerateContentConfig(**config),
            )
        )
        text = getattr(response, "text", None)
        if not isinstance(text, str):
            raise ProviderResponseError("provider returned no JSON")
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("provider returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise ProviderResponseError("provider returned a non-object JSON value")
        return value

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        response = await _with_transient_retry(
            lambda: self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(**kwargs) if kwargs else None,
            )
        )
        embeddings = getattr(response, "embeddings", None)
        if not embeddings:
            raise ProviderResponseError("provider returned no embedding")
        values = getattr(embeddings[0], "values", None)
        if not isinstance(values, list) or not all(isinstance(value, (int, float)) for value in values):
            raise ProviderResponseError("provider returned an invalid embedding")
        return [float(value) for value in values]


class GeminiProvider(_GoogleGenAIProvider):
    """Gemini Developer API adapter using GEMINI_API_KEY."""

    def __init__(self, settings: Settings, client_factory: ClientFactory = genai.Client) -> None:
        if not settings.gemini_api_key:
            raise ProviderConfigurationError("Gemini API credentials are not configured")
        client = client_factory(api_key=settings.gemini_api_key)
        super().__init__(client, settings.gemini_text_model, settings.gemini_json_model, settings.gemini_embedding_model)


class VertexProvider(_GoogleGenAIProvider):
    """Vertex AI adapter using ADC or GOOGLE_APPLICATION_CREDENTIALS."""

    def __init__(self, settings: Settings, client_factory: ClientFactory = genai.Client) -> None:
        if not settings.vertex_project:
            raise ProviderConfigurationError("Vertex AI project is not configured")
        client = client_factory(vertexai=True, project=settings.vertex_project, location=settings.vertex_location)
        super().__init__(client, settings.vertex_text_model, settings.vertex_json_model, settings.vertex_embedding_model)
