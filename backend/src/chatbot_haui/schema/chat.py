from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from chatbot_haui.schema.base import ApiModel


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = Field(default=None, alias="conversationId", max_length=36)  # trống = tạo cuộc mới

    model_config = {"populate_by_name": True}


class ConversationOut(ApiModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationRename(BaseModel):
    title: str = Field(min_length=1, max_length=120, pattern=r"\S")


class ChatMessageOut(ApiModel):
    id: int
    role: Literal["user", "bot"]
    content: str
    created_at: datetime
