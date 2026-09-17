from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from chatbot_haui.core.config import settings


def create_llm(temperature: float | None = None) -> BaseChatModel:
    """Tạo chat model theo LLM_PROVIDER (google | groq)."""
    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.google_model, google_api_key=settings.google_api_key, temperature=temperature
        )
    from langchain_groq import ChatGroq
    return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=temperature)


@lru_cache
def get_llm() -> BaseChatModel:
    return create_llm()
