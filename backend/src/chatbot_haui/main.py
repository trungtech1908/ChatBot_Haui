import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from chatbot_haui.ai import observability
from chatbot_haui.ai.graph import init_graph
from chatbot_haui.api.router import api_router
from chatbot_haui.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _preload():
    """Nạp model embedding, client Qdrant, schema view: tốn vài chục giây, không để request đầu tiên chịu."""
    from chatbot_haui.ai.embedding import get_embedder
    from chatbot_haui.ai.tools.rag import get_qdrant
    from chatbot_haui.ai.tools.text2sql import view_columns

    get_embedder()
    get_qdrant()
    view_columns()


async def _preload_background():
    try:
        await asyncio.to_thread(_preload)
        logger.info("Đã nạp xong model embedding và schema")
    except Exception:
        logger.exception("Nạp sẵn lỗi, sẽ nạp khi có câu hỏi đầu tiên")


def _checkpointer_conninfo() -> str:
    # psycopg nhận URL dạng postgresql://; bỏ tên driver của SQLAlchemy
    return settings.db_url.replace("postgresql+psycopg://", "postgresql://", 1)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Bộ nhớ phiên của graph: checkpointer LangGraph lưu vào chính PostgreSQL của hệ thống
    async with AsyncConnectionPool(
        _checkpointer_conninfo(), max_size=10, open=False,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        init_graph(checkpointer)
        task = asyncio.create_task(_preload_background()) if settings.rag_preload else None
        yield
        if task:
            task.cancel()
        observability.flush()


app = FastAPI(title="ChatBot HaUI API", lifespan=lifespan)
app.include_router(api_router)
