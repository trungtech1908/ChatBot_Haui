"""Bộ nhớ dài hạn: Mem0 OSS chạy in-process, vector store là Qdrant (ARCHITECTURE mục 2.10).

Quy tắc "được lưu / không được lưu" được thực thi ở nhiều chỗ, không chỉ dựa vào prompt:
  Định danh   user_id = HMAC(MEMORY_SALT, ma_sv) — trên cloud không có mã sinh viên thật
  Trích xuất  tự trích bằng LLM nhỏ theo schema cố định 4 loại (prompts/memory_extract.py)
  Lọc khi ghi is_allowed(): còn chữ số / từ khóa nhạy cảm → bỏ
  Ghi         Mem0 add(infer=False): Mem0 chỉ embed + lưu, không tự suy luận, không lưu nguyên văn hội thoại
  Lọc khi đọc chạy lại is_allowed() trên kết quả search trước khi đưa vào prompt
  Xóa         forget(): delete_all(user_id)

Vì sao không dùng add(infer=True) của Mem0: bản 2.x chỉ thêm (không cập nhật/xóa) và lưu nguyên văn
tin nhắn vào SQLite cục bộ — nguyên văn đó có thể chứa số liệu, hoàn cảnh bị cấm lưu.
History của Mem0 để trong RAM (':memory:') nên không có bản sao nào nằm trên đĩa.
"""
import asyncio
import hashlib
import hmac
import logging
import re
import unicodedata
from functools import lru_cache
from typing import Literal

from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from chatbot_haui.ai.embedding import DIMS, embed
from chatbot_haui.ai.llm import get_model, structured
from chatbot_haui.ai.prompts import memory_extract
from chatbot_haui.core.config import settings

logger = logging.getLogger(__name__)

TOP_K = 5
# Memory mới giống memory cũ tới mức này thì coi là trùng, không ghi thêm
DUPLICATE_SCORE = 0.9

# So khớp trên chữ đã bỏ dấu, để bắt cả khi sinh viên gõ không dấu
_BLOCKED = [
    "ho ngheo", "can ngheo", "khuyet tat", "dan toc", "mo coi", "benh", "tai nan", "thuong binh", "liet si",
    "hoan canh", "kho khan", "tro cap", "ky luat", "khien trach", "canh cao", "dinh chi", "thoi hoc", "canh bao",
    "dien thoai", "sdt", "dia chi", "can cuoc", "cccd", "cmnd", "ngay sinh", "email", "ho ten",
    # thông tin về người khác
    "sinh vien khac", "nguoi khac", "ban khac", "ban be", "ban cung lop",
]
_DIGIT = re.compile(r"\d")


def _strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    return "".join(c for c in text if not unicodedata.combining(c))


def is_allowed(text: str) -> bool:
    """False nếu memory chứa con số hoặc thuộc nhóm "không được lưu"."""
    if not text.strip() or _DIGIT.search(text) or "@" in text:
        return False
    plain = f" {_strip_accents(text)} "
    return not any(re.search(rf"\b{kw}\b", plain) for kw in _BLOCKED)


def user_key(ma_sv: str) -> str:
    return hmac.new(settings.memory_salt.encode(), ma_sv.encode(), hashlib.sha256).hexdigest()[:32]


class _BgeEmbeddings(Embeddings):
    """Bọc bge-m3 đã nạp trong app để Mem0 dùng chung, không nạp model lần hai."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return embed([text])[0]


@lru_cache
def get_memory():
    from mem0 import Memory

    from chatbot_haui.ai.tools.rag import get_qdrant

    return Memory.from_config({
        "vector_store": {"provider": "qdrant", "config": {
            "client": get_qdrant(), "collection_name": settings.qdrant_memory_collection, "embedding_model_dims": DIMS,
        }},
        "embedder": {"provider": "langchain", "config": {"model": _BgeEmbeddings()}},
        # Không được gọi vì luôn add(infer=False); vẫn phải cấu hình để Mem0 khởi tạo được
        "llm": {"provider": "langchain", "config": {"model": get_model("small")}},
        "history_db_path": ":memory:",
    })


class MemoryItem(BaseModel):
    loai: Literal["giao_tiep", "chu_de", "muc_tieu", "cau_hoi_do_dang"]
    noi_dung: str = Field(description="Một câu ngắn, ngôi thứ ba, bắt đầu bằng 'Sinh viên'")


class Extraction(BaseModel):
    muc: list[MemoryItem] = Field(default_factory=list)


@lru_cache
def _extractor():
    prompt = ChatPromptTemplate.from_messages([("system", memory_extract.SYSTEM), ("human", memory_extract.HUMAN)])
    return prompt | structured("small", Extraction)


def _search_sync(key: str, query: str, top_k: int) -> list[dict]:
    return get_memory().search(query, filters={"user_id": key}, top_k=top_k).get("results", [])


async def recall(key: str, query: str) -> list[str]:
    """Memory liên quan tới câu hỏi, đã lọc lại. Lỗi thì trả rỗng — memory không được làm hỏng câu trả lời."""
    if not settings.memory_ready:
        return []
    try:
        results = await asyncio.to_thread(_search_sync, key, query, TOP_K)
    except Exception:
        logger.exception("Đọc memory lỗi")
        return []
    kept = [r["memory"] for r in results if is_allowed(r["memory"])]
    if len(kept) < len(results):
        logger.warning("Bỏ %d memory không qua bộ lọc khi đọc", len(results) - len(kept))
    return kept


async def remember(key: str, user_message: str, assistant_message: str, config: dict | None = None) -> list[str]:
    """Trích + lọc + ghi. Chạy nền sau khi đã trả lời; trả về các memory đã ghi (để log/test)."""
    if not settings.memory_ready:
        return []
    extraction: Extraction = await _extractor().ainvoke(
        {"user": user_message, "assistant": assistant_message}, config=config)
    saved = []
    for item in extraction.muc:
        text = item.noi_dung.strip()
        if not is_allowed(text):
            logger.info("Memory bị bộ lọc chặn (loại %s)", item.loai)
            continue
        similar = await asyncio.to_thread(_search_sync, key, text, 1)
        if similar and similar[0].get("score", 0) >= DUPLICATE_SCORE:
            continue
        await asyncio.to_thread(
            get_memory().add, [{"role": "user", "content": text}], user_id=key, infer=False, metadata={"loai": item.loai},
        )
        saved.append(text)
    return saved


async def forget(key: str) -> None:
    """Xóa toàn bộ memory của một sinh viên (khi sinh viên yêu cầu xóa dữ liệu)."""
    if settings.memory_ready:
        await asyncio.to_thread(get_memory().delete_all, user_id=key)
