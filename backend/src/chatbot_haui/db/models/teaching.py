"""Giảng dạy: giảng viên, lịch học, lịch thi, thực tập.

Nhóm bảng này KHÔNG có trong haui_db/01_schema.sql gốc — được bổ sung để phục vụ các trang
Lịch học / Lịch thi / Thực tập của frontend và 3 view chatbot v_lich_hoc, v_lich_thi, v_thuc_tap.
Thông tin định danh của giảng viên (email, sdt) không đưa vào view chatbot.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR, BigInteger, Boolean, CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, Base


class GiangVien(Base):
    __tablename__ = "giang_vien"
    __table_args__ = (
        CheckConstraint("hoc_vi IN ('ths', 'ts', 'pgs', 'gs')", name="ck_giang_vien_hoc_vi"),
        CORE,
    )

    ma_gv: Mapped[str] = mapped_column(String(10), primary_key=True)
    ho_ten: Mapped[str] = mapped_column(String(60))
    ma_khoa: Mapped[str] = mapped_column(String(10), ForeignKey("core.khoa.ma_khoa"))
    hoc_vi: Mapped[str | None] = mapped_column(String(5))
    # Thông tin liên hệ: không đưa vào view chatbot
    email: Mapped[str | None] = mapped_column(String(100))
    sdt: Mapped[str | None] = mapped_column(String(15))


class LichHoc(Base):
    """Lịch học hằng tuần của lớp học phần. thu: 2..7 = thứ Hai..thứ Bảy, 8 = Chủ nhật."""
    __tablename__ = "lich_hoc"
    __table_args__ = (
        CheckConstraint("thu BETWEEN 2 AND 8", name="ck_lich_hoc_thu"),
        CheckConstraint("tiet_bd BETWEEN 1 AND 15", name="ck_lich_hoc_tiet_bd"),
        CheckConstraint("so_tiet BETWEEN 1 AND 6", name="ck_lich_hoc_so_tiet"),
        CheckConstraint("tuan_kt IS NULL OR tuan_bd IS NULL OR tuan_kt >= tuan_bd", name="ck_lich_hoc_tuan"),
        UniqueConstraint("ma_lop", "thu", "tiet_bd", name="uq_lich_hoc_ca"),
        Index("ix_lich_hoc_lop", "ma_lop"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_lop: Mapped[str] = mapped_column(String(20), ForeignKey("core.lop_hp.ma_lop"))
    thu: Mapped[int] = mapped_column(SmallInteger)
    tiet_bd: Mapped[int] = mapped_column(SmallInteger)
    so_tiet: Mapped[int] = mapped_column(SmallInteger)
    phong: Mapped[str | None] = mapped_column(String(20))
    tuan_bd: Mapped[int | None] = mapped_column(SmallInteger)  # tuần thứ mấy trong học kỳ
    tuan_kt: Mapped[int | None] = mapped_column(SmallInteger)


class LichThi(Base):
    """Ca thi của lớp học phần. lan_thi = 2 là thi lại."""
    __tablename__ = "lich_thi"
    __table_args__ = (
        CheckConstraint("lan_thi IN (1, 2)", name="ck_lich_thi_lan"),
        CheckConstraint("so_phut BETWEEN 15 AND 300", name="ck_lich_thi_so_phut"),
        CheckConstraint(
            "hinh_thuc IN ('tu_luan', 'trac_nghiem', 'van_dap', 'thuc_hanh', 'tieu_luan')",
            name="ck_lich_thi_hinh_thuc",
        ),
        UniqueConstraint("ma_lop", "lan_thi", name="uq_lich_thi_lop_lan"),
        Index("ix_lich_thi_lop", "ma_lop"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_lop: Mapped[str] = mapped_column(String(20), ForeignKey("core.lop_hp.ma_lop"))
    lan_thi: Mapped[int] = mapped_column(SmallInteger, default=1, server_default="1")
    thoi_gian: Mapped[datetime]
    so_phut: Mapped[int] = mapped_column(SmallInteger)
    hinh_thuc: Mapped[str] = mapped_column(String(15))
    phong: Mapped[str | None] = mapped_column(String(20))


class LichThiSv(Base):
    """SV trong ca thi: số báo danh, vị trí, điều kiện dự thi.

    ly_do chỉ điền khi du_dieu_kien = false (VD nợ học phí, thiếu điểm quá trình).
    """
    __tablename__ = "lich_thi_sv"
    __table_args__ = (
        CheckConstraint("so_bd > 0", name="ck_lich_thi_sv_so_bd"),
        CheckConstraint("du_dieu_kien OR ly_do IS NOT NULL", name="ck_lich_thi_sv_ly_do"),
        Index("ix_lich_thi_sv_sv", "ma_sv"),
        CORE,
    )

    ma_lich_thi: Mapped[int] = mapped_column(BigInteger, ForeignKey("core.lich_thi.id"), primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), primary_key=True)
    so_bd: Mapped[int] = mapped_column(SmallInteger)
    vi_tri: Mapped[str | None] = mapped_column(String(10))
    du_dieu_kien: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    ly_do: Mapped[str | None] = mapped_column(String(200))


class DoanhNghiep(Base):
    __tablename__ = "doanh_nghiep"
    __table_args__ = CORE

    ma_dn: Mapped[str] = mapped_column(String(10), primary_key=True)
    ten: Mapped[str] = mapped_column(String(150))
    dia_chi: Mapped[str | None] = mapped_column(String(255))
    linh_vuc: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(100))
    sdt: Mapped[str | None] = mapped_column(String(15))


class ThucTap(Base):
    """Kỳ thực tập của SV tại doanh nghiệp, gắn với học phần thực tập trong CTĐT."""
    __tablename__ = "thuc_tap"
    __table_args__ = (
        CheckConstraint(
            "trang_thai IN ('dang_thuc_tap', 'hoan_thanh', 'huy')", name="ck_thuc_tap_trang_thai"
        ),
        CheckConstraint("diem BETWEEN 0 AND 10", name="ck_thuc_tap_diem"),
        CheckConstraint("den_ngay IS NULL OR den_ngay >= tu_ngay", name="ck_thuc_tap_ngay"),
        Index("ix_thuc_tap_sv", "ma_sv"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    ma_dn: Mapped[str] = mapped_column(String(10), ForeignKey("core.doanh_nghiep.ma_dn"))
    ma_hk: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"))
    ma_mon: Mapped[str | None] = mapped_column(String(10), ForeignKey("core.mon.ma_mon"))
    ma_gv: Mapped[str | None] = mapped_column(String(10), ForeignKey("core.giang_vien.ma_gv"))  # GV hướng dẫn
    vi_tri: Mapped[str | None] = mapped_column(String(100))
    tu_ngay: Mapped[date]
    den_ngay: Mapped[date | None]
    trang_thai: Mapped[str] = mapped_column(String(15), default="dang_thuc_tap", server_default="dang_thuc_tap")
    diem: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
