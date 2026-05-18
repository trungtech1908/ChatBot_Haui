"""Xác thực sinh viên — maSV lấy từ tài khoản đăng nhập, không từ .env."""

from __future__ import annotations

import getpass

from chatbot_haui.auth.session import StudentSession
from chatbot_haui.db.engine import SessionLocal
from chatbot_haui.db.models import SinhVien, TaiKhoan


def authenticate(ten_tai_khoan: str, mat_khau: str) -> StudentSession | None:
    ten = (ten_tai_khoan or "").strip()
    if not ten or not mat_khau:
        return None

    db = SessionLocal()
    try:
        acc = db.query(TaiKhoan).filter(TaiKhoan.tenTaiKhoan == ten).first()
        if not acc or (acc.matKhau or "") != mat_khau:
            return None
        ma_sv = (acc.maSV or "").strip()
        if not ma_sv:
            return None
        sv = db.query(SinhVien).filter(SinhVien.maSV == ma_sv).first()
        ho_ten = sv.hoTen.strip() if sv and sv.hoTen else None
        return StudentSession(
            ma_sv=ma_sv,
            ho_ten=ho_ten,
            ten_tai_khoan=ten,
        )
    finally:
        db.close()


def login_interactive(max_attempts: int = 3) -> StudentSession:
    """CLI: nhập tài khoản/mật khẩu cho đến khi đúng hoặc hết lượt."""
    for attempt in range(1, max_attempts + 1):
        print(f"Đăng nhập ({attempt}/{max_attempts})")
        ten = input("Tên tài khoản: ").strip()
        mk = getpass.getpass("Mật khẩu: ")
        session = authenticate(ten, mk)
        if session:
            label = session.ho_ten or session.ma_sv
            print(f"Xin chào, {label} ({session.ma_sv})\n")
            return session
        print("Sai tài khoản hoặc mật khẩu.\n")
    raise SystemExit("Đăng nhập thất bại.")
