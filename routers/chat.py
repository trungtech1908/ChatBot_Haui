from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import json
import os

router = APIRouter(prefix="/api") # Các đường dẫn trong này sẽ có tiền tố /api
CHAT_FILE = "json/chat_data.json"

class ChatMessage(BaseModel):
    username: str
    message: str

class DeleteChatRequest(BaseModel):
    username: str

@router.post("/send_message")
async def send_message(chat_data: ChatMessage):
    messages = []
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                messages = json.load(f)
        except:
            messages = []

    new_msg = {
        "username": chat_data.username,
        "message": chat_data.message,
        "timestamp": datetime.now().strftime("%H:%M %d/%m/%Y"),
        "sender": "user"
    }
    messages.append(new_msg)

    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    return {"status": "success", "data": new_msg}

@router.post("/reset_chat")
async def reset_chat(data: DeleteChatRequest):
    if not os.path.exists(CHAT_FILE):
        return {"status": "success", "message": "File không tồn tại"}

    try:
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            all_messages = json.load(f)
    except:
        all_messages = []

    # Giữ lại tin nhắn không phải của user này
    remaining = [msg for msg in all_messages if msg.get("username") != data.username]

    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)

    return {"status": "success", "message": "Đã xóa lịch sử chat"}