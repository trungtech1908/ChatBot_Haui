"""Tạo chat model.

Hai cỡ model (ARCHITECTURE mục 3, ngân sách LLM), mỗi cỡ có thể ở provider khác nhau để chia quota:
  main  — Planner, Text2SQL, Generator, Validator          provider: LLM_PROVIDER
  small — Rewriter, Router, RAG judge, trích xuất memory,  provider: LLM_PROVIDER_SMALL (trống = LLM_PROVIDER)
          tóm tắt hội thoại

Mỗi cỡ có fallback sang provider còn lại (nếu có API key): model quá tải (503) hoặc hết quota (429)
thì câu trả lời chậm đi chứ không hỏng. Mọi request có timeout để không treo vô hạn.
Code gọi LLM dùng text() / structured() — không gọi thẳng model — để luôn có fallback.
"""
from functools import lru_cache
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

from chatbot_haui.core.config import settings

Size = Literal["main", "small"]
Provider = Literal["google", "groq"]

# Model nhỏ mặc định theo provider, dùng khi LLM_MODEL_SMALL để trống / cho fallback của model nhỏ
DEFAULT_SMALL = {"groq": "openai/gpt-oss-20b", "google": "gemini-3.5-flash-lite"}
TIMEOUT = 60  # giây / request


def provider(size: Size) -> Provider:
    return (settings.llm_provider_small or settings.llm_provider) if size == "small" else settings.llm_provider


def model_name(size: Size, p: Provider | None = None) -> str:
    p = p or provider(size)
    if size == "small":
        return settings.llm_model_small if p == provider("small") and settings.llm_model_small else DEFAULT_SMALL[p]
    return settings.google_model if p == "google" else settings.groq_model


def _has_key(p: Provider) -> bool:
    return bool(settings.google_api_key if p == "google" else settings.groq_api_key)


def create_llm(p: Provider, name: str, max_retries: int = 2) -> BaseChatModel:
    if p == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        # Gemini 3.x khuyến nghị giữ temperature mặc định (1.0); hạ xuống dễ làm model lặp hoặc suy luận kém
        extra = {} if name.startswith("gemini-3") else {"temperature": 0}
        return ChatGoogleGenerativeAI(
            model=name, google_api_key=settings.google_api_key, max_retries=max_retries, timeout=TIMEOUT, **extra,
        )
    from langchain_groq import ChatGroq
    return ChatGroq(model=name, api_key=settings.groq_api_key, temperature=0, max_retries=max_retries, timeout=TIMEOUT)


@lru_cache
def get_model(size: Size = "main") -> BaseChatModel:
    """Model chính của cỡ này, không kèm fallback (cho thư viện cần đúng một BaseChatModel, VD Mem0)."""
    # Có fallback thì nhường provider kia sớm: Groq 429 kèm retry-after 14–40s nên không thử lại;
    # Gemini 503 (quá tải) thường hết sau vài giây nên thử lại 1 lần
    p = provider(size)
    retries = 2 if not _fallback_provider(size) else (0 if p == "groq" else 1)
    return create_llm(p, model_name(size), max_retries=retries)


def _fallback_provider(size: Size) -> Provider | None:
    other: Provider = "groq" if provider(size) == "google" else "google"
    return other if _has_key(other) else None


@lru_cache
def _fallback_model(size: Size) -> BaseChatModel | None:
    p = _fallback_provider(size)
    return create_llm(p, model_name(size, p)) if p else None


def text(size: Size = "main") -> Runnable:
    """Model trả text, có fallback."""
    fb = _fallback_model(size)
    return get_model(size).with_fallbacks([fb]) if fb else get_model(size)


def structured(size: Size, schema) -> Runnable:
    """Model trả về đúng schema Pydantic, có fallback (mỗi model tự bọc structured output của nó)."""
    primary = get_model(size).with_structured_output(schema)
    fb = _fallback_model(size)
    return primary.with_fallbacks([fb.with_structured_output(schema)]) if fb else primary
