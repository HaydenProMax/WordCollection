from app.config import get_settings
from app.llm.base import LLMProvider
from app.llm.openai_provider import OpenAIProvider


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.model_provider == "openai":
        return OpenAIProvider(settings)
    raise RuntimeError(f"Unsupported model provider: {settings.model_provider}")
