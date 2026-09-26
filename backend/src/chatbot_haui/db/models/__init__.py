"""Import tất cả model để Alembic nhận đủ bảng.

Ba schema, theo haui_db/ARCHITECTURE.md mục 4.2:
  core    — bảng nghiệp vụ
  private — tai_khoan, không cấp quyền cho chatbot
  public  — bảng do app sở hữu (chat_message, checkpointer LangGraph)
"""
from chatbot_haui.db.models.academic import DangKy, DiemHp, DkTotNghiep, KetQuaHk, LopHp, RenLuyen, ThangDiem
from chatbot_haui.db.models.catalog import Ctdt, CtdtMon, HocKy, Khoa, KhoiNganh, Mon, Nganh, NhomTuChon, NienKhoa
from chatbot_haui.db.models.chat import ChatConversation, ChatMessage
from chatbot_haui.db.models.finance import DonGia, GiaoDich, HeSoTc, KhoanThu, PhaiThu
from chatbot_haui.db.models.policy import ChinhSach, DoiTuong, MucTran, SvChinhSach, SvDoiTuong, ThamSo
from chatbot_haui.db.models.scholarship import HocBong, LoaiHb, MucHb
from chatbot_haui.db.models.student import BienDong, KyLuat, SinhVien, TaiKhoan, ThanhTich
from chatbot_haui.db.models.teaching import DoanhNghiep, GiangVien, LichHoc, LichThi, LichThiSv, ThucTap

__all__ = [
    # catalog
    "Khoa", "KhoiNganh", "Nganh", "NienKhoa", "Ctdt", "HocKy", "Mon", "NhomTuChon", "CtdtMon",
    # student
    "SinhVien", "TaiKhoan", "BienDong", "KyLuat", "ThanhTich",
    # academic
    "ThangDiem", "LopHp", "DangKy", "DiemHp", "KetQuaHk", "RenLuyen", "DkTotNghiep",
    # scholarship
    "LoaiHb", "MucHb", "HocBong",
    # policy
    "DoiTuong", "SvDoiTuong", "ChinhSach", "SvChinhSach", "MucTran", "ThamSo",
    # finance
    "HeSoTc", "DonGia", "KhoanThu", "PhaiThu", "GiaoDich",
    # teaching
    "GiangVien", "LichHoc", "LichThi", "LichThiSv", "DoanhNghiep", "ThucTap",
    # app
    "ChatConversation",
    "ChatMessage",
]
