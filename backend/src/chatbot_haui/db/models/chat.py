"""Lịch sử hội thoại hiển thị trên giao diện.

Bộ nhớ phiên của graph (6 lượt gần nhất + tóm tắt cuộn) do checkpointer LangGraph giữ,
bảng này chỉ để frontend vẽ lại khung chat.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import Base


class ChatMessage(Base):
    __tablename__ = "chat_message"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), ForeignKey("private.tai_khoan.ten_dn", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(10))  # user | bot
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
