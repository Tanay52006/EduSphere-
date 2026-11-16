import json
from typing import Any

import httpx

from app.ai.provider import ProviderResponseError


class OllamaProvider:
    def __init__(self, base_url: str = "http://localhost:11434", transport: httpx.AsyncBaseTransport | None = None, model: str = "llama3.2") -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport
        self.model = model

    async def generate_text(self, prompt: str, **kwargs: Any) -> str:
        payload = {"model": self.model, "prompt": prompt, "stream": False, **kwargs}
        async with httpx.AsyncClient(transport=self.transport, timeout=30.0) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
        return str(response.json().get("response", ""))

    async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> dict[str, Any]:
        output_format = schema.model_json_schema() if hasattr(schema, "model_json_schema") else "json"
        text = await self.generate_text(prompt, format=output_format, **kwargs)
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderResponseError("provider returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise ProviderResponseError("provider returned a non-object JSON value")
        return value

    async def embed(self, text: str, **kwargs: Any) -> list[float]:
        payload = {"model": self.model, "prompt": text}
        async with httpx.AsyncClient(transport=self.transport, timeout=30.0) as client:
            response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
            response.raise_for_status()
        return list(response.json().get("embedding", []))
