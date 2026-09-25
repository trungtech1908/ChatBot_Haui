"""Sinh viên, tài khoản đăng nhập, biến động học vụ, kỷ luật, thành tích."""
from datetime import date

from sqlalchemy import CHAR, BigInteger, CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, PRIVATE, Base


class SinhVien(Base):
    """Thông tin cá nhân (ngay_sinh, email, sdt, dia_chi, dan_toc) KHÔNG đưa vào view chatbot."""
    __tablename__ = "sinh_vien"
    __table_args__ = (
        CheckConstraint(
            "trang_thai IN ('dang_hoc', 'bao_luu', 'dinh_chi', 'thoi_hoc', 'tot_nghiep')",
            name="ck_sinh_vien_trang_thai",
        ),
        CheckConstraint("hb_dau_vao IN ('toan_khoa', 'nam_nhat', '5_trieu')", name="ck_sinh_vien_hb_dau_vao"),
        CORE,
    )

    ma_sv: Mapped[str] = mapped_column(String(12), primary_key=True)
    ho_ten: Mapped[str] = mapped_column(String(60))
    ma_ctdt: Mapped[str] = mapped_column(String(15), ForeignKey("core.ctdt.ma_ctdt"))
    # CTĐT thứ hai (không xét học bổng)
    ma_ctdt_2: Mapped[str | None] = mapped_column(String(15), ForeignKey("core.ctdt.ma_ctdt"))
    lop: Mapped[str | None] = mapped_column(String(20))  # lớp hành chính
    ngay_nhap_hoc: Mapped[date]
    trang_thai: Mapped[str] = mapped_column(String(15), default="dang_hoc", server_default="dang_hoc")
    hb_dau_vao: Mapped[str | None] = mapped_column(String(15))  # diện HB HaUI
    # --- Thông tin cá nhân ---
    ngay_sinh: Mapped[date | None]
    email: Mapped[str | None] = mapped_column(String(100))
    sdt: Mapped[str | None] = mapped_column(String(15))
    dia_chi: Mapped[str | None] = mapped_column(String(255))
    dan_toc: Mapped[str | None] = mapped_column(String(30))
    quoc_tich: Mapped[str | None] = mapped_column(String(50))


class TaiKhoan(Base):
    """Tài khoản đăng nhập. Schema private: không cấp quyền cho role chatbot."""
    __tablename__ = "tai_khoan"
    __table_args__ = PRIVATE

    ten_dn: Mapped[str] = mapped_column(String(50), primary_key=True)
    # NULL với tài khoản không phải sinh viên
    ma_sv: Mapped[str | None] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), unique=True)
    mat_khau: Mapped[str] = mapped_column(String(255))  # đã hash (argon2)


class BienDong(Base):
    """Quyết định học vụ: bảo lưu, trở lại, thôi học, tốt nghiệp."""
    __tablename__ = "bien_dong"
    __table_args__ = (
        CheckConstraint(
            "loai IN ('bao_luu', 'tro_lai', 'thoi_hoc', 'buoc_thoi_hoc', 'chuyen_nganh', 'tot_nghiep')",
            name="ck_bien_dong_loai",
        ),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    loai: Mapped[str] = mapped_column(String(15))
    so_qd: Mapped[str | None] = mapped_column(String(30))
    ngay_qd: Mapped[date]
    tu_ngay: Mapped[date]
    den_ngay: Mapped[date | None]


class KyLuat(Base):
    """noi_dung KHÔNG đưa vào view chatbot (không lộ nội dung vi phạm)."""
    __tablename__ = "ky_luat"
    __table_args__ = (
        CheckConstraint(
            "hinh_thuc IN ('khien_trach', 'canh_cao', 'dinh_chi', 'buoc_thoi_hoc')", name="ck_ky_luat_hinh_thuc"
        ),
        Index("ix_ky_luat_sv", "ma_sv"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    hinh_thuc: Mapped[str] = mapped_column(String(15))
    so_qd: Mapped[str] = mapped_column(String(30))
    ngay_qd: Mapped[date]
    # khiển trách +3 tháng, cảnh cáo +6 tháng; buộc thôi học: NULL
    het_hieu_luc: Mapped[date | None]
    noi_dung: Mapped[str | None] = mapped_column(Text)


class ThanhTich(Base):
    """Giải thưởng dùng xét học bổng."""
    __tablename__ = "thanh_tich"
    __table_args__ = (
        CheckConstraint("loai IN ('nckh', 'tay_nghe', 'olympic', 'khac')", name="ck_thanh_tich_loai"),
        CheckConstraint("cap IN ('truong', 'tinh', 'quoc_gia', 'khu_vuc', 'quoc_te')", name="ck_thanh_tich_cap"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    nam_hoc: Mapped[str] = mapped_column(CHAR(9))
    loai: Mapped[str] = mapped_column(String(15))
    cap: Mapped[str] = mapped_column(String(10))
    giai: Mapped[str] = mapped_column(String(20))  # 'nhat', 'nhi', 'ba', 'khuyen_khich'
    cuoc_thi: Mapped[str | None] = mapped_column(String(200))
