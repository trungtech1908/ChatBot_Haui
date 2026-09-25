"""Hội thoại: chạy graph, lưu lịch sử hiển thị, ghi bộ nhớ dài hạn chạy nền.

Không stream token của Generator: Validator chạy SAU Generator và có thể bắt viết lại, nên chỉ gửi câu
trả lời đã qua kiểm định. Trong lúc chờ, client nhận sự kiện trạng thái từng bước.
"""
import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from chatbot_haui.ai import memory, observability
from chatbot_haui.ai.graph import STAGES, get_graph, load_profile, turn_input
from chatbot_haui.db.models import ChatMessage, TaiKhoan
from chatbot_haui.db.session import SessionLocal

logger = logging.getLogger(__name__)
ERROR_REPLY = "Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau."
# Tham chiếu mạnh tới task nền, tránh bị thu gom khi chưa chạy xong
_background: set[asyncio.Task] = set()


@dataclass
class ChatEvent:
    kind: str  # status | answer
    text: str


class ChatError(Exception):
    pass


def list_messages(db: Session, username: str) -> list[ChatMessage]:
    return list(db.scalars(select(ChatMessage).where(ChatMessage.username == username).order_by(ChatMessage.id)))


async def clear_messages(db: Session, username: str):
    db.execute(delete(ChatMessage).where(ChatMessage.username == username))
    db.commit()
    # Xóa luôn bộ nhớ phiên của graph, nếu không lượt sau vẫn "nhớ" hội thoại đã xóa
    checkpointer = get_graph().checkpointer
    if checkpointer is not None:
        await checkpointer.adelete_thread(username)


async def forget(account: TaiKhoan):
    """Xóa bộ nhớ dài hạn (Mem0) của sinh viên."""
    await memory.forget(memory.user_key(account.ma_sv))


def _save(username: str, role: str, content: str):
    # Session riêng: stream chạy sau khi session của request đã đóng
    with SessionLocal() as db:
        db.add(ChatMessage(username=username, role=role, content=content))
        db.commit()


def _remember_later(key: str, question: str, answer: str, config: dict):
    async def job():
        try:
            saved = await memory.remember(key, question, answer, config)
            if saved:
                logger.info("Đã ghi %d memory", len(saved))
        except Exception:
            logger.exception("Ghi memory lỗi (không ảnh hưởng câu trả lời)")
        finally:
            observability.flush()

    task = asyncio.create_task(job())
    _background.add(task)
    task.add_done_callback(_background.discard)


async def reply(account: TaiKhoan, message: str) -> AsyncIterator[ChatEvent]:
    """Lưu câu hỏi → chạy graph (phát trạng thái) → phát câu trả lời → lưu. Lỗi thì lưu thông báo lỗi và raise ChatError."""
    username = account.ten_dn
    _save(username, "user", message)
    key = memory.user_key(account.ma_sv)
    config = {
        "configurable": {"thread_id": username},
        "callbacks": observability.callbacks(),
        "metadata": observability.trace_metadata(key, session_id=key),
        "run_name": "chatbot_turn",
    }
    graph = get_graph()
    try:
        profile = await load_profile(account.ma_sv)
        inputs = turn_input(message, account.ma_sv, key, profile)
        answer = None
        async for event in graph.astream_events(inputs, config, version="v2"):
            node = event["metadata"].get("langgraph_node")
            if event["event"] == "on_chain_start" and event["name"] == node and node in STAGES:
                yield ChatEvent("status", STAGES[node])
            elif event["event"] == "on_chain_end" and not event.get("parent_ids"):
                answer = (event["data"].get("output") or {}).get("answer")  # state cuối của run gốc
        if not answer:
            raise RuntimeError("Graph kết thúc mà không có câu trả lời")
    except Exception as e:
        logger.exception("Chatbot lỗi khi trả lời")
        _save(username, "bot", ERROR_REPLY)
        observability.flush()
        raise ChatError(ERROR_REPLY) from e

    yield ChatEvent("answer", answer)
    _save(username, "bot", answer)
    _remember_later(key, message, answer,
                    {"callbacks": config["callbacks"], "metadata": config["metadata"], "run_name": "memory_write"})
