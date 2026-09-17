from fastapi import APIRouter, HTTPException, status

from chatbot_haui.api.deps import DbSession
from chatbot_haui.core.security import create_access_token
from chatbot_haui.schema.auth import LoginRequest, Token
from chatbot_haui.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(body: LoginRequest, db: DbSession) -> Token:
    account = auth_service.authenticate(db, body.username, body.password)
    if not account:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sai tài khoản hoặc mật khẩu")
    return Token(access_token=create_access_token(account.tenTaiKhoan))
