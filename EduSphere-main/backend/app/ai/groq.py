import asyncio
import json
import logging
from typing import Any

import httpx
from pydantic import TypeAdapter

from app.ai.provider import LLMProvider, ProviderConfigurationError, ProviderResponseError

logger = logging.getLogger("edusphere.ai.groq")


def response_schema(schema: Any) -> dict[str, Any]:
    value = schema.model_json_schema() if hasattr(schema, "model_json_schema") else TypeAdapter(schema).json_schema()
    strict = True

    def close_objects(node: Any) -> None:
        nonlocal strict
        if isinstance(node, list):
            for child in node:
                close_objects(child)
        elif isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                if isinstance(node.get("additionalProperties"), dict) or "properties" not in node:
                    strict = False  # Dynamic maps in activity blueprints need best-effort mode.
                else:
                    node["additionalProperties"] = False
                    node["required"] = list(node["properties"])
            for child in node.values():
                close_objects(child)

    close_objects(value)
    return {"type": "json_schema", "json_schema": {"name": "response", "strict": strict, "schema": value}}


class GroqProvider:
    def __init__(self, api_key: str | None, model: str = "openai/gpt-oss-120b", transport: httpx.AsyncBaseTransport | None = None,
                 *, embedding_provider: LLMProvider | None = None, base_url: str = "https://api.groq.com") -> None:
        if not api_key or not api_key.strip():
            raise ProviderConfigurationError("GROQ_API_KEY is required for the Groq provider")
        self._api_key = api_key
        self.model = model
        self.transport = transport
        self.embedding_provider = embedding_provider
        self.base_url = base_url.rstrip("/")

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_completion_tokens": 12000,
            "reasoning_effort": "medium",
            **kwargs,
        }
        try:
            async with httpx.AsyncClient(transport=self.transport, timeout=120.0) as client:
                for attempt in range(3):
                    response = await client.post(
                        f"{self.base_url}/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self._api_key}"}, json=payload,
                    )
                    if response.status_code != 429 or attempt == 2:
                        break
                    delay = float(response.headers.get("retry-after", "5"))
                    if not 0 <= delay <= 60:
                        break
                    await asyncio.sleep(delay)
            if response.status_code != 200:
                logger.warning("groq request rejected status=%s", response.status_code)
                raise ProviderResponseError(f"Groq request failed (HTTP {response.status_code})")
            choice = response.json()["choices"][0]
            content = choice["message"].get("content")
            if choice.get("finish_reason") != "stop" or not isinstance(content, str) or not content.strip():
                raise ProviderResponseError("Groq returned incomplete or empty content")
            return content
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            raise ProviderResponseError("Groq request failed or returned an invalid response") from None

    async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> dict[str, Any]:
        content = await self.generate_text(prompt, response_format=response_schema(schema), **kwargs)
        try:
            value = json.loads(content)
        except json.JSONDecodeError:
            raise ProviderResponseError("Groq returned invalid JSON") from None
        if not isinstance(value, dict):
            raise ProviderResponseError("Groq returned a non-object JSON value")
        return value

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        if self.embedding_provider is not None:
            return await self.embedding_provider.embed(text, **kwargs)
        raise ProviderConfigurationError("Groq does not provide embeddings; configure an embedding-capable provider for ingestion and semantic search")
