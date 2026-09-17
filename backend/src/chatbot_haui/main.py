import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from chatbot_haui.ai.graph import get_graph
from chatbot_haui.api.router import api_router
from chatbot_haui.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _preload_rag():
    try:
        await asyncio.to_thread(get_graph)
        logger.info("Đã nạp xong RAG")
    except Exception:
        logger.exception("Không nạp được RAG, sẽ thử lại khi có câu hỏi")
        get_graph.cache_clear()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Nạp model embedding/LLM ở nền để app nhận request ngay
    task = asyncio.create_task(_preload_rag()) if settings.rag_preload else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="ChatBot HaUI API", lifespan=lifespan)
app.include_router(api_router)
