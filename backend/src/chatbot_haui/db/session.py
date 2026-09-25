"""Kết nối PostgreSQL.

Hai engine tách biệt, đúng theo haui_db/ARCHITECTURE.md mục 6:
  engine          — role owner, dùng cho auth và API sinh viên (đọc schema core/private)
  chatbot_engine  — role chatbot_reader, CHỈ thấy schema chatbot; Text2SQL chạy ở đây
"""
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Connection, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from chatbot_haui.core.config import settings

# Dùng cho __table_args__ của model
CORE = {"schema": "core"}
PRIVATE = {"schema": "private"}

engine = create_engine(settings.db_url, pool_pre_ping=True, pool_recycle=3600)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


_chatbot_engine = None


def chatbot_engine():
    """Engine role chatbot_reader. Tạo lười vì chỉ Text2SQL cần."""
    global _chatbot_engine
    if _chatbot_engine is None:
        _chatbot_engine = create_engine(
            settings.db_chatbot_url, pool_pre_ping=True, pool_recycle=3600,
            # Không để transaction treo giữ connection
            connect_args={"options": "-c statement_timeout=5000"},
        )
    return _chatbot_engine


@contextmanager
def chatbot_scope(ma_sv: str) -> Iterator[Connection]:
    """Transaction READ ONLY đã gắn app.ma_sv — phạm vi dữ liệu mà view v_* lọc theo.

    ma_sv luôn đến từ session đăng nhập, không bao giờ từ prompt (ARCHITECTURE mục 2.1).
    READ ONLY nên dù SQL của LLM lọt qua validator cũng không ghi được.
    """
    with chatbot_engine().connect() as conn:
        with conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            conn.execute(text("SELECT set_config('app.ma_sv', :ma_sv, true)"), {"ma_sv": ma_sv})
            yield conn
