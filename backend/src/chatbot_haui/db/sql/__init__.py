"""Các file SQL thô mà Alembic thực thi (view, function, phân quyền)."""
from pathlib import Path

SQL_DIR = Path(__file__).parent


def read_sql(name: str) -> str:
    return (SQL_DIR / name).read_text(encoding="utf-8")
