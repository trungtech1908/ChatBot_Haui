from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from chatbot_haui.schema.base import ApiModel


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageOut(ApiModel):
    id: int
    role: Literal["user", "bot"]
    content: str
    created_at: datetime
