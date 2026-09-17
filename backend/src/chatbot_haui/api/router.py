from fastapi import APIRouter

from chatbot_haui.api.routes import auth, chat, students

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(students.router)
api_router.include_router(chat.router)


@api_router.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
