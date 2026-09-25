"""Model embedding bge-m3 dùng chung cho RAG (dense) và bộ nhớ dài hạn.

Nạp một lần (~2GB RAM); mọi nơi gọi get_embedder() thay vì tự tạo model.
"""
import threading

from chatbot_haui.core.config import settings

DIMS = 1024  # bge-m3 dense


_model = None
_lock = threading.Lock()


def get_embedder():
    # lru_cache không chặn hai luồng cùng khởi tạo lần đầu (preload nền + request đầu tiên) → nạp model 2 lần
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from FlagEmbedding import BGEM3FlagModel
                _model = BGEM3FlagModel(settings.embedding_model, use_fp16=False, devices="cpu")
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    """Đồng bộ, tốn CPU: gọi qua asyncio.to_thread khi đang ở trong event loop."""
    return [v.tolist() for v in get_embedder().encode(texts, max_length=1024)["dense_vecs"]]
