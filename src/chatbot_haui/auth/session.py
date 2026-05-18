"""Phiên sinh viên sau đăng nhập — dùng cho RAG, CSDL và Zep."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StudentSession:
    """Một sinh viên đã xác thực."""

    ma_sv: str
    ho_ten: Optional[str] = None
    ten_tai_khoan: Optional[str] = None
    thread_id: Optional[str] = None

    @property
    def zep_user_id(self) -> str:
        return self.ma_sv

    @property
    def zep_thread_id(self) -> str:
        if self.thread_id:
            return self.thread_id
        return f"chat_{self.ma_sv}"


def resolve_session_ids(
    session: StudentSession | None = None,
    *,
    ma_sv: str | None = None,
    thread_id: str | None = None,
) -> tuple[str, str, str]:
    """
    Trả về (ma_sv, zep_user_id, zep_thread_id).
    Bắt buộc có session hoặc ma_sv — không đọc từ .env.
    """
    if session is not None:
        return session.ma_sv, session.zep_user_id, session.zep_thread_id or f"chat_{session.ma_sv}"
    if ma_sv:
        ma = ma_sv.strip()
        return ma, ma, thread_id or f"chat_{ma}"
    raise ValueError(
        "Chưa có phiên sinh viên. Gọi authenticate() sau đăng nhập "
        "hoặc truyền StudentSession vào run_agent()."
    )
