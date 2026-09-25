import json

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from chatbot_haui.api.deps import CurrentStudent, DbSession
from chatbot_haui.schema.chat import ChatMessageOut, ChatRequest
from chatbot_haui.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(data: dict, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/messages")
def messages(db: DbSession, account: CurrentStudent) -> list[ChatMessageOut]:
    return chat_service.list_messages(db, account.ten_dn)


@router.delete("/messages", status_code=status.HTTP_204_NO_CONTENT)
async def clear(db: DbSession, account: CurrentStudent):
    """Xóa lịch sử chat và bộ nhớ phiên (6 lượt gần nhất) của graph."""
    await chat_service.clear_messages(db, account.ten_dn)


@router.delete("/memory", status_code=status.HTTP_204_NO_CONTENT)
async def forget(account: CurrentStudent):
    """Xóa bộ nhớ dài hạn (sở thích, chủ đề, mục tiêu) mà chatbot ghi nhớ về sinh viên."""
    await chat_service.forget(account)


@router.post("")
async def send(body: ChatRequest, account: CurrentStudent) -> StreamingResponse:
    """SSE: `event: status` + `{"stage": "..."}` cho từng bước xử lý, rồi `data: {"delta": "..."}` là câu trả lời
    đã qua kiểm định, kết thúc bằng `event: done` hoặc `event: error` kèm `{"message": "..."}`."""
    async def events():
        try:
            async for event in chat_service.reply(account, body.message):
                if event.kind == "status":
                    yield _sse({"stage": event.text}, "status")
                else:
                    yield _sse({"delta": event.text})
            yield _sse({}, "done")
        except chat_service.ChatError as e:
            yield _sse({"message": str(e)}, "error")

    return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})
