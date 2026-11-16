from app.ai.google_genai import GeminiProvider, VertexProvider
from app.ai.groq import GroqProvider
from app.ai.mock import MockProvider
from app.ai.ollama import OllamaProvider
from app.ai.provider import LLMProvider, ProviderConfigurationError
from app.core.config import Settings


def create_provider(settings: Settings) -> LLMProvider:
    provider_name = "vertex" if settings.gemini_use_vertex else settings.llm_provider
    if provider_name == "mock":
        return MockProvider()
    if provider_name == "groq":
        embeddings = GeminiProvider(settings) if settings.gemini_api_key else None
        return GroqProvider(settings.groq_api_key.get_secret_value() if settings.groq_api_key else None,
                            model=settings.groq_model, embedding_provider=embeddings, base_url=settings.groq_base_url)
    if provider_name == "ollama":
        return OllamaProvider(base_url=settings.ollama_base_url, model=settings.ollama_model)
    if provider_name == "gemini":
        return GeminiProvider(settings)
    if provider_name == "vertex":
        return VertexProvider(settings)
    raise ProviderConfigurationError(f"unsupported LLM provider: {provider_name}")
