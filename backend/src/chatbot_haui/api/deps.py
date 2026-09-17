from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from chatbot_haui.core.security import decode_access_token
from chatbot_haui.db.models import TaiKhoan
from chatbot_haui.db.session import get_db

bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_account(db: DbSession, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> TaiKhoan:
    username = decode_access_token(credentials.credentials) if credentials else None
    account = db.get(TaiKhoan, username) if username else None
    if not account:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ", {"WWW-Authenticate": "Bearer"})
    return account


CurrentAccount = Annotated[TaiKhoan, Depends(get_current_account)]
