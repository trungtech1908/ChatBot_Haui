"""Lịch sử hội thoại hiển thị trên giao diện, chia theo cuộc trò chuyện.

Bộ nhớ phiên của graph (6 lượt gần nhất + tóm tắt cuộn) do checkpointer LangGraph giữ theo thread_id = id cuộc
trò chuyện; các bảng này chỉ để frontend liệt kê cuộc trò chuyện và vẽ lại khung chat.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import Base


class ChatConversation(Base):
    __tablename__ = "chat_conversation"

    # UUID: dùng làm thread_id của checkpointer và session của trace; không đoán được như số tăng dần
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(
        String(50), ForeignKey("private.tai_khoan.ten_dn", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())  # lần có tin nhắn mới nhất


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), ForeignKey("private.tai_khoan.ten_dn", ondelete="CASCADE"), index=True
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_conversation.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(10))  # user | bot
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
