"""Danh mục đào tạo: khoa, ngành, niên khóa, CTĐT, học kỳ, môn (schema core).

Quy ước tên và giá trị theo haui_db/01_schema.sql:
  ma_hk 'YYYYk' — YYYY năm bắt đầu năm học; k = 1,2 HK chính, 3,4 HK phụ
"""
from datetime import date

from sqlalchemy import CHAR, Boolean, CheckConstraint, ForeignKey, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, Base


class Khoa(Base):
    """Đơn vị đào tạo (Khoa/Trường/Trung tâm)."""
    __tablename__ = "khoa"
    __table_args__ = CORE

    ma_khoa: Mapped[str] = mapped_column(String(10), primary_key=True)
    ten: Mapped[str] = mapped_column(String(100))


class KhoiNganh(Base):
    """Khối ngành để tra mức trần miễn giảm học phí (NĐ 97/2023)."""
    __tablename__ = "khoi_nganh"
    __table_args__ = (
        CheckConstraint("bac IN ('dai_hoc', 'cao_dang')", name="ck_khoi_nganh_bac"),
        CORE,
    )

    ma_khoi: Mapped[str] = mapped_column(String(20), primary_key=True)
    bac: Mapped[str] = mapped_column(String(10))
    ten: Mapped[str] = mapped_column(String(200))


class Nganh(Base):
    __tablename__ = "nganh"
    __table_args__ = (
        CheckConstraint("khoi_ntb IN ('ky_thuat', 'xa_hoi')", name="ck_nganh_khoi_ntb"),
        CORE,
    )

    ma_nganh: Mapped[str] = mapped_column(String(10), primary_key=True)
    ten: Mapped[str] = mapped_column(String(150))
    ma_khoa: Mapped[str] = mapped_column(String(10), ForeignKey("core.khoa.ma_khoa"))
    ma_khoi: Mapped[str] = mapped_column(String(20), ForeignKey("core.khoi_nganh.ma_khoi"))
    # Khối chia quỹ học bổng Nguyễn Thanh Bình
    khoi_ntb: Mapped[str] = mapped_column(String(10))


class NienKhoa(Base):
    """Khóa tuyển sinh: 'Cử nhân K19' = (dai_hoc, 19), 'Kỹ sư K2' = (ky_su, 2)."""
    __tablename__ = "nien_khoa"
    __table_args__ = (
        CheckConstraint("bac IN ('dai_hoc', 'ky_su', 'cao_dang')", name="ck_nien_khoa_bac"),
        CORE,
    )

    ma_nk: Mapped[str] = mapped_column(String(10), primary_key=True)  # 'DH-K19'
    bac: Mapped[str] = mapped_column(String(10))
    so_khoa: Mapped[int] = mapped_column(SmallInteger)
    nam_nhap_hoc: Mapped[int] = mapped_column(SmallInteger)


class Ctdt(Base):
    """Chương trình đào tạo."""
    __tablename__ = "ctdt"
    __table_args__ = (
        CheckConstraint("hinh_thuc IN ('chinh_quy', 'vlvh', 'tu_xa')", name="ck_ctdt_hinh_thuc"),
        CheckConstraint("loai IN ('dai_tra', 'tieng_anh')", name="ck_ctdt_loai"),
        CORE,
    )

    ma_ctdt: Mapped[str] = mapped_column(String(15), primary_key=True)
    ten: Mapped[str] = mapped_column(String(150))
    ma_nganh: Mapped[str] = mapped_column(String(10), ForeignKey("core.nganh.ma_nganh"))
    ma_nk: Mapped[str] = mapped_column(String(10), ForeignKey("core.nien_khoa.ma_nk"))
    hinh_thuc: Mapped[str] = mapped_column(String(10))
    loai: Mapped[str] = mapped_column(String(10))
    so_tc: Mapped[int] = mapped_column(SmallInteger)  # tổng TC yêu cầu tốt nghiệp
    so_hk: Mapped[int] = mapped_column(SmallInteger)  # số HK thiết kế; HB chỉ xét trong khoảng này


class HocKy(Base):
    __tablename__ = "hoc_ky"
    __table_args__ = (
        CheckConstraint("loai IN ('chinh', 'phu')", name="ck_hoc_ky_loai"),
        # HK chính phải trỏ về chính nó
        CheckConstraint("loai = 'phu' OR ma_hk_chinh = ma_hk", name="ck_hoc_ky_chinh_tu_tro"),
        CORE,
    )

    ma_hk: Mapped[str] = mapped_column(CHAR(5), primary_key=True)  # '20251'
    nam_hoc: Mapped[str] = mapped_column(CHAR(9))  # '2025-2026'
    loai: Mapped[str] = mapped_column(String(5))
    ten: Mapped[str] = mapped_column(String(50))
    # HK chính mà kết quả được gộp vào (HK chính = chính nó)
    ma_hk_chinh: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"))
    ngay_bd: Mapped[date | None]
    ngay_kt: Mapped[date | None]


class Mon(Base):
    """Môn học. Tín chỉ thành phần dùng tính TC học phí, cờ xet_hb theo QĐ 725 Điều 4."""
    __tablename__ = "mon"
    __table_args__ = (
        CheckConstraint("so_tc > 0", name="ck_mon_so_tc"),
        CheckConstraint(
            "loai IN ('thuong', 'gdtc', 'gdqp', 'cntt', 'ngoai_ngu', 'thuc_tap', 'do_an')", name="ck_mon_loai"
        ),
        CheckConstraint("tc_lt + tc_dac_thu + tc_th = so_tc", name="ck_mon_tong_tc"),
        CORE,
    )

    ma_mon: Mapped[str] = mapped_column(String(10), primary_key=True)
    ten: Mapped[str] = mapped_column(String(150))
    so_tc: Mapped[int] = mapped_column(SmallInteger)
    # Lý thuyết, tiểu luận/BTL, GDTC, GDQP → hệ số 1,0
    tc_lt: Mapped[float] = mapped_column(Numeric(3, 1), default=0, server_default="0")
    # Ngoại ngữ, thực tập, đồ án → hệ số 1,5
    tc_dac_thu: Mapped[float] = mapped_column(Numeric(3, 1), default=0, server_default="0")
    # Thực hành, thí nghiệm → hệ số 2,5
    tc_th: Mapped[float] = mapped_column(Numeric(3, 1), default=0, server_default="0")
    loai: Mapped[str] = mapped_column(String(15), default="thuong", server_default="thuong")
    # false: chỉ xếp P/F, không tính điểm TB
    tinh_tb: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    # false: GDTC, GDQP, CNTT, ngoại ngữ... không tính điểm xét HB
    xet_hb: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class NhomTuChon(Base):
    __tablename__ = "nhom_tu_chon"
    __table_args__ = CORE

    ma_nhom: Mapped[str] = mapped_column(String(15), primary_key=True)
    ma_ctdt: Mapped[str] = mapped_column(String(15), ForeignKey("core.ctdt.ma_ctdt"))
    ten: Mapped[str] = mapped_column(String(100))
    so_tc: Mapped[int] = mapped_column(SmallInteger)  # số TC phải chọn trong nhóm


class CtdtMon(Base):
    """Môn thuộc CTĐT."""
    __tablename__ = "ctdt_mon"
    __table_args__ = (
        CheckConstraint("bat_buoc OR ma_nhom IS NOT NULL", name="ck_ctdt_mon_nhom"),
        CORE,
    )

    ma_ctdt: Mapped[str] = mapped_column(String(15), ForeignKey("core.ctdt.ma_ctdt"), primary_key=True)
    ma_mon: Mapped[str] = mapped_column(String(10), ForeignKey("core.mon.ma_mon"), primary_key=True)
    bat_buoc: Mapped[bool] = mapped_column(Boolean)
    ma_nhom: Mapped[str | None] = mapped_column(String(15), ForeignKey("core.nhom_tu_chon.ma_nhom"))
    hk_thu: Mapped[int | None] = mapped_column(SmallInteger)  # học kỳ thứ mấy theo kế hoạch chuẩn
