"""Hội thoại: quản lý cuộc trò chuyện, chạy graph, lưu lịch sử hiển thị, ghi bộ nhớ dài hạn chạy nền.

Mỗi cuộc trò chuyện là một thread của checkpointer (thread_id = id cuộc trò chuyện), nên bộ nhớ phiên
(6 lượt + tóm tắt) tách riêng từng cuộc; bộ nhớ dài hạn Mem0 vẫn theo sinh viên, dùng chung mọi cuộc.

Client nhận tiến trình từng bước và token câu trả lời ngay khi Generator sinh ra (ai/progress.py). Validator
chạy sau nên bản nháp có thể bị bác → `reset` rồi stream bản mới; cuối lượt luôn gửi `answer` là câu trả lời
cuối cùng (đã qua kiểm định hoặc câu dự phòng) — đây cũng là nội dung được lưu.
"""
import asyncio
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from chatbot_haui.ai import memory, observability
from chatbot_haui.ai.graph import get_graph, load_profile, turn_input
from chatbot_haui.ai.progress import Progress
from chatbot_haui.db.models import ChatConversation, ChatMessage, TaiKhoan
from chatbot_haui.db.session import SessionLocal

logger = logging.getLogger(__name__)
ERROR_REPLY = "Xin lỗi, hệ thống đang gặp sự cố. Vui lòng thử lại sau."
# Tham chiếu mạnh tới task nền, tránh bị thu gom khi chưa chạy xong
_background: set[asyncio.Task] = set()
TITLE_LEN = 60


@dataclass
class ChatEvent:
    kind: str  # conversation | step | delta | reset | answer
    data: dict


class ChatError(Exception):
    pass


def make_title(message: str) -> str:
    """Tiêu đề cuộc trò chuyện từ câu hỏi đầu tiên: gọn một dòng, cắt ở ranh giới từ."""
    text = re.sub(r"\s+", " ", message).strip()
    if len(text) <= TITLE_LEN:
        return text or "Cuộc trò chuyện mới"
    cut = text[:TITLE_LEN].rsplit(" ", 1)[0] or text[:TITLE_LEN]
    return cut.rstrip(" ,.;:") + "…"


def list_conversations(db: Session, username: str) -> list[ChatConversation]:
    return list(db.scalars(
        select(ChatConversation).where(ChatConversation.username == username)
        .order_by(ChatConversation.updated_at.desc(), ChatConversation.created_at.desc())))


def get_conversation(db: Session, username: str, conversation_id: str) -> ChatConversation | None:
    """Chỉ trả về cuộc trò chuyện của chính tài khoản này; của người khác coi như không tồn tại."""
    conv = db.get(ChatConversation, conversation_id)
    return conv if conv is not None and conv.username == username else None


def list_messages(db: Session, conversation: ChatConversation) -> list[ChatMessage]:
    return list(db.scalars(
        select(ChatMessage).where(ChatMessage.conversation_id == conversation.id).order_by(ChatMessage.id)))


def rename_conversation(db: Session, conversation: ChatConversation, title: str) -> ChatConversation:
    conversation.title = re.sub(r"\s+", " ", title).strip()
    db.commit()
    return conversation


async def _delete_threads(ids: list[str]):
    # Xóa luôn bộ nhớ phiên của graph, nếu không mở lại id cũ vẫn "nhớ" hội thoại đã xóa
    checkpointer = get_graph().checkpointer
    if checkpointer is not None:
        for thread_id in ids:
            await checkpointer.adelete_thread(thread_id)


async def delete_conversation(db: Session, conversation: ChatConversation):
    db.delete(conversation)  # tin nhắn xóa theo ON DELETE CASCADE
    db.commit()
    await _delete_threads([conversation.id])


async def delete_all_conversations(db: Session, username: str):
    conversations = list_conversations(db, username)
    for conv in conversations:
        db.delete(conv)
    db.commit()
    await _delete_threads([c.id for c in conversations])


def open_conversation(db: Session, username: str, conversation_id: str | None, message: str) -> tuple[ChatConversation, bool]:
    """Cuộc trò chuyện cho câu hỏi này: id có sẵn (phải của chính tài khoản) hoặc tạo mới từ câu hỏi đầu tiên.

    Trả về (cuộc trò chuyện, có phải vừa tạo). Không tìm thấy → ValueError.
    """
    if conversation_id:
        conv = get_conversation(db, username, conversation_id)
        if conv is None:
            raise ValueError("Không tìm thấy cuộc trò chuyện")
        return conv, False
    conv = ChatConversation(username=username, title=make_title(message))
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv, True


async def forget(account: TaiKhoan):
    """Xóa bộ nhớ dài hạn (Mem0) của sinh viên."""
    await memory.forget(memory.user_key(account.ma_sv))


def _save(username: str, conversation_id: str, role: str, content: str):
    # Session riêng: stream chạy sau khi session của request đã đóng
    with SessionLocal() as db:
        db.add(ChatMessage(username=username, conversation_id=conversation_id, role=role, content=content))
        db.execute(update(ChatConversation).where(ChatConversation.id == conversation_id).values(updated_at=func.now()))
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


async def reply(account: TaiKhoan, conversation: ChatConversation, created: bool, message: str) -> AsyncIterator[ChatEvent]:
    """Lưu câu hỏi → chạy graph (phát tiến trình và token câu trả lời) → phát câu trả lời cuối → lưu.

    Cuộc trò chuyện vừa tạo thì phát `conversation` đầu tiên để client biết id. Lỗi thì lưu thông báo lỗi và raise ChatError.
    """
    username = account.ten_dn
    if created:
        yield ChatEvent("conversation", {"id": conversation.id, "title": conversation.title})
    _save(username, conversation.id, "user", message)
    key = memory.user_key(account.ma_sv)
    config = {
        "configurable": {"thread_id": conversation.id},
        "callbacks": observability.callbacks(),
        "metadata": observability.trace_metadata(key, session_id=conversation.id),
        "run_name": "chatbot_turn",
    }
    graph = get_graph()
    try:
        profile = await load_profile(account.ma_sv)
        inputs = turn_input(message, account.ma_sv, key, profile)
        answer = None
        progress = Progress()
        async for event in graph.astream_events(inputs, config, version="v2"):
            for out in progress.feed(event):
                yield ChatEvent(out.kind, out.data)
            if event["event"] == "on_chain_end" and not event.get("parent_ids"):
                answer = (event["data"].get("output") or {}).get("answer")  # state cuối của run gốc
        if not answer:
            raise RuntimeError("Graph kết thúc mà không có câu trả lời")
    except Exception as e:
        logger.exception("Chatbot lỗi khi trả lời")
        _save(username, conversation.id, "bot", ERROR_REPLY)
        observability.flush()
        raise ChatError(ERROR_REPLY) from e

    yield ChatEvent("answer", {"text": answer})
    _save(username, conversation.id, "bot", answer)
    _remember_later(key, message, answer,
                    {"callbacks": config["callbacks"], "metadata": config["metadata"], "run_name": "memory_write"})
