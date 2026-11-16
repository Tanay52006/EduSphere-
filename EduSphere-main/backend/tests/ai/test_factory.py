import pytest

from app.ai.factory import create_provider
from app.ai.google_genai import GeminiProvider, VertexProvider
from app.ai.groq import GroqProvider
from app.ai.mock import MockProvider
from app.ai.ollama import OllamaProvider
from app.ai.provider import ProviderConfigurationError
from app.core.config import Settings


@pytest.mark.parametrize(
    ("name", "expected"),
    [("mock", MockProvider), ("ollama", OllamaProvider)],
)
def test_offline_provider_selection(name: str, expected: type[object]) -> None:
    assert isinstance(create_provider(Settings(_env_file=None, llm_provider=name)), expected)


def test_google_provider_selection_is_config_driven() -> None:
    assert isinstance(create_provider(Settings(_env_file=None, llm_provider="gemini", gemini_api_key="placeholder")), GeminiProvider)
    assert isinstance(create_provider(Settings(_env_file=None, llm_provider="vertex", vertex_project="project")), VertexProvider)


def test_groq_provider_selection_is_config_driven() -> None:
    settings = Settings(_env_file=None, llm_provider="groq", groq_api_key="placeholder", gemini_api_key="placeholder")
    assert isinstance(create_provider(settings), GroqProvider)


def test_gemini_use_vertex_overrides_default_provider() -> None:
    assert isinstance(create_provider(Settings(_env_file=None, gemini_use_vertex=True, vertex_project="project")), VertexProvider)


def test_unknown_provider_fails_safely() -> None:
    with pytest.raises(ProviderConfigurationError, match="unsupported LLM provider"):
        create_provider(Settings(_env_file=None, llm_provider="unknown"))
