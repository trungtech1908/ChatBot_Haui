"""Trace Langfuse cho mọi node/LLM call (ARCHITECTURE mục 8).

Dữ liệu định danh được che TRƯỚC khi rời tiến trình (hàm mask của Langfuse SDK):
  - mã sinh viên (10 chữ số bắt đầu bằng 20), email, số điện thoại → nhãn thay thế
  - giá trị của các khóa ma_sv, ho_ten, ngay_sinh, sdt, email, dia_chi trong dict/list
Điểm, số tiền trong kết quả SQL vẫn giữ nguyên vì cần để debug; user_id trên Langfuse là HMAC.
"""
import logging
import re
from functools import lru_cache
from typing import Any

from chatbot_haui.core.config import settings

logger = logging.getLogger(__name__)

_PATTERNS = [
    (re.compile(r"\b20\d{8}\b"), "[MA_SV]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"(?<!\d)(?:\+?84|0)\d{9,10}(?!\d)"), "[SDT]"),
]
_SENSITIVE_KEYS = {"ma_sv", "ho_ten", "ngay_sinh", "sdt", "email", "dia_chi"}


def mask(*, data: Any, **_: Any) -> Any:
    if isinstance(data, str):
        for pattern, label in _PATTERNS:
            data = pattern.sub(label, data)
        return data
    if isinstance(data, dict):
        return {k: "[AN]" if k in _SENSITIVE_KEYS else mask(data=v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return type(data)(mask(data=v) for v in data)
    return data


@lru_cache
def langfuse_client():
    if not settings.langfuse_ready:
        return None
    from langfuse import Langfuse
    return Langfuse(
        public_key=settings.langfuse_public_key, secret_key=settings.langfuse_secret_key,
        base_url=settings.langfuse_base_url, mask=mask,
    )


def callbacks() -> list:
    """Callback LangChain gắn vào config của graph; rỗng nếu Langfuse tắt hoặc thiếu key."""
    if langfuse_client() is None:
        return []
    from langfuse.langchain import CallbackHandler
    return [CallbackHandler()]


def trace_metadata(user_key: str, session_id: str, tags: list[str] | None = None) -> dict:
    return {"langfuse_user_id": user_key, "langfuse_session_id": session_id, "langfuse_tags": tags or ["chatbot"]}


def flush() -> None:
    client = langfuse_client()
    if client is not None:
        try:
            client.flush()
        except Exception:
            logger.exception("Flush Langfuse lỗi")
