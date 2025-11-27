from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import json
import os
from fastapi.responses import StreamingResponse
from graph import stream_graph  # Import stream_graph từ graph.py

router = APIRouter(prefix="/api")
CHAT_FILE = "json/chat_data.json"

# Dict lưu query mới nhất của user (global để stream dùng)
latest_query = {}  # {username: query}

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

    # Lưu query để stream
    latest_query[chat_data.username] = chat_data.message

    return {"status": "success", "data": new_msg}

@router.post("/save_bot_response")
async def save_bot_response(chat_data: ChatMessage):
    """Lưu câu trả lời của bot vào lịch sử chat"""
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
        "sender": "bot"
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

    remaining = [msg for msg in all_messages if msg.get("username") != data.username]

    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)

    # Xóa query nếu có
    latest_query.pop(data.username, None)

    return {"status": "success", "message": "Đã xóa lịch sử chat"}

@router.get("/stream/{username}")
async def stream(username: str):
    if username not in latest_query:
        async def empty_stream():
            yield "data: Không có tin nhắn mới\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(empty_stream(), media_type="text/event-stream")

    query = latest_query.pop(username)

    async def format_stream():
        """Format output từ stream_graph thành SSE format"""
        try:
            async for chunk in stream_graph(query, username):
                if chunk:
                    # Format theo SSE: data: <content>\n\n
                    yield f"data: {chunk}\n\n"
            # Gửi signal kết thúc
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: Lỗi: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(format_stream(), media_type="text/event-stream")