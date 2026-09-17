import json

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse

from chatbot_haui.api.deps import CurrentAccount, DbSession
from chatbot_haui.schema.chat import ChatMessageOut, ChatRequest
from chatbot_haui.services import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


def _sse(data: dict, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/messages")
def messages(db: DbSession, account: CurrentAccount) -> list[ChatMessageOut]:
    return chat_service.list_messages(db, account.tenTaiKhoan)


@router.delete("/messages", status_code=status.HTTP_204_NO_CONTENT)
def clear(db: DbSession, account: CurrentAccount):
    chat_service.clear_messages(db, account.tenTaiKhoan)


@router.post("")
async def send(body: ChatRequest, account: CurrentAccount) -> StreamingResponse:
    """Stream câu trả lời dạng SSE: `data: {"delta": "..."}` cho từng token, kết thúc bằng `event: done`
    hoặc `event: error` kèm `{"message": "..."}`."""
    async def events():
        try:
            async for token in chat_service.reply(account.tenTaiKhoan, body.message):
                yield _sse({"delta": token})
            yield _sse({}, "done")
        except chat_service.ChatError as e:
            yield _sse({"message": str(e)}, "error")

    return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})
