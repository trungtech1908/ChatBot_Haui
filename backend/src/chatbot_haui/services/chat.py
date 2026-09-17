import logging
from collections.abc import AsyncIterator

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from chatbot_haui.ai.graph import stream
from chatbot_haui.db.models import ChatMessage
from chatbot_haui.db.session import SessionLocal

logger = logging.getLogger(__name__)
ERROR_REPLY = "Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau."


def list_messages(db: Session, username: str) -> list[ChatMessage]:
    return list(db.scalars(select(ChatMessage).where(ChatMessage.username == username).order_by(ChatMessage.id)))


def clear_messages(db: Session, username: str):
    db.execute(delete(ChatMessage).where(ChatMessage.username == username))
    db.commit()


def _save(username: str, role: str, content: str):
    # Session riêng: stream chạy sau khi session của request đã đóng
    with SessionLocal() as db:
        db.add(ChatMessage(username=username, role=role, content=content))
        db.commit()


class ChatError(Exception):
    pass


async def reply(username: str, message: str) -> AsyncIterator[str]:
    """Lưu câu hỏi, stream câu trả lời từ RAG, lưu câu trả lời khi xong. RAG lỗi thì lưu và raise ChatError."""
    _save(username, "user", message)
    answer = []
    try:
        async for token in stream(message):
            answer.append(token)
            yield token
    except Exception as e:
        logger.exception("RAG lỗi khi trả lời")
        _save(username, "bot", ERROR_REPLY)
        raise ChatError(ERROR_REPLY) from e
    _save(username, "bot", "".join(answer))
