import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from chatbot_haui.api.deps import CurrentStudent, DbSession
from chatbot_haui.schema.chat import ChatMessageOut, ChatRequest, ConversationOut, ConversationRename
from chatbot_haui.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(data: dict, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _owned(db, account, conversation_id: str):
    conv = chat_service.get_conversation(db, account.ten_dn, conversation_id)
    if conv is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cuộc trò chuyện")
    return conv


@router.get("/conversations")
def conversations(db: DbSession, account: CurrentStudent) -> list[ConversationOut]:
    """Các cuộc trò chuyện của sinh viên, mới hoạt động gần nhất trước."""
    return chat_service.list_conversations(db, account.ten_dn)


@router.get("/conversations/{conversation_id}/messages")
def messages(conversation_id: str, db: DbSession, account: CurrentStudent) -> list[ChatMessageOut]:
    return chat_service.list_messages(db, _owned(db, account, conversation_id))


@router.patch("/conversations/{conversation_id}")
def rename(conversation_id: str, body: ConversationRename, db: DbSession, account: CurrentStudent) -> ConversationOut:
    return chat_service.rename_conversation(db, _owned(db, account, conversation_id), body.title)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(conversation_id: str, db: DbSession, account: CurrentStudent):
    """Xóa một cuộc trò chuyện cùng bộ nhớ phiên (6 lượt gần nhất) của graph."""
    await chat_service.delete_conversation(db, _owned(db, account, conversation_id))


@router.delete("/conversations", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all(db: DbSession, account: CurrentStudent):
    await chat_service.delete_all_conversations(db, account.ten_dn)


@router.delete("/memory", status_code=status.HTTP_204_NO_CONTENT)
async def forget(account: CurrentStudent):
    """Xóa bộ nhớ dài hạn (sở thích, chủ đề, mục tiêu) mà chatbot ghi nhớ về sinh viên."""
    await chat_service.forget(account)


@router.post("")
async def send(body: ChatRequest, db: DbSession, account: CurrentStudent) -> StreamingResponse:
    """Gửi câu hỏi vào cuộc trò chuyện `conversationId` (trống = tạo cuộc mới; không phải của mình → 404).

    SSE, mỗi sự kiện một dòng `event:` + `data:` JSON:
    - `conversation` `{"id", "title"}`: chỉ khi vừa tạo cuộc mới, luôn là sự kiện đầu tiên
    - `step` `{"id", "label", "status": running|done|error, "detail"}`: bước đang/đã làm (cùng id là cập nhật)
    - `delta` `{"text"}`: token câu trả lời, nối vào phần đang hiện
    - `reset` `{}`: bản nháp bị bác hoặc model chạy lại — xóa phần câu trả lời đã hiện
    - `answer` `{"text"}`: câu trả lời cuối cùng, thay toàn bộ phần đã hiện
    - kết thúc bằng `done`, hoặc `error` kèm `{"message"}`."""
    try:
        conversation, created = chat_service.open_conversation(db, account.ten_dn, body.conversation_id, body.message)
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e

    async def events():
        try:
            async for event in chat_service.reply(account, conversation, created, body.message):
                yield _sse(event.data, event.kind)
            yield _sse({}, "done")
        except chat_service.ChatError as e:
            yield _sse({"message": str(e)}, "error")

    return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})
