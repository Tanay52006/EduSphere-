from collections.abc import Mapping
from typing import Any, Protocol


class ProviderConfigurationError(RuntimeError):
    """Raised when a provider cannot be initialized safely from configuration."""


class ProviderResponseError(RuntimeError):
    """Raised when an upstream response cannot be mapped to the provider contract."""


class LLMProvider(Protocol):
    async def generate_json(self, schema: Any, prompt: str, **kwargs: Any) -> Mapping[str, Any]: ...
    async def generate_text(self, prompt: str, **kwargs: Any) -> str: ...
    async def embed(self, text: str, **kwargs: Any) -> list[float]: ...


class UsageBudget(Protocol):
    async def reserve(self, user_id: str, estimated_tokens: int) -> bool: ...


class NoOpUsageBudget:
    async def reserve(self, user_id: str, estimated_tokens: int) -> bool:
        return True
