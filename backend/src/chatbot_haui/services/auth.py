from sqlalchemy.orm import Session

from chatbot_haui.core.security import verify_password
from chatbot_haui.db.models import TaiKhoan


def authenticate(db: Session, username: str, password: str) -> TaiKhoan | None:
    account = db.get(TaiKhoan, username)
    if account and account.mat_khau and verify_password(password, account.mat_khau):
        return account
    return None
