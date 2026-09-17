# Import tất cả model để relationship dạng chuỗi và Alembic nhận đủ bảng
from chatbot_haui.db.models.academic import (
    CT_CTDT, CT_DT, CT_NMH, TQMH, GiangVien, KetQuaHocKy, KetQuaMonHoc, Khoa, LichHoc, LichThi, LichThiSV, LopHoc,
    MonHoc, NhomMH, PhuTrach, SinhVienLopHoc,
)
from chatbot_haui.db.models.chat import ChatMessage
from chatbot_haui.db.models.finance import LSGD, GiaoDich, KhoangThuKhac, TaiChinh
from chatbot_haui.db.models.internship import DoanhNghiep, ThucTap
from chatbot_haui.db.models.student import DieuKienTotNghiep, DoiTuong, SinhVien, TaiKhoan

__all__ = [
    "CT_CTDT", "CT_DT", "CT_NMH", "TQMH", "GiangVien", "KetQuaHocKy", "KetQuaMonHoc", "Khoa", "LichHoc", "LichThi",
    "LichThiSV", "LopHoc", "MonHoc", "NhomMH", "PhuTrach", "SinhVienLopHoc", "ChatMessage", "LSGD", "GiaoDich",
    "KhoangThuKhac", "TaiChinh", "DoanhNghiep", "ThucTap", "DieuKienTotNghiep", "DoiTuong", "SinhVien", "TaiKhoan",
]
