"""Học tập: thang điểm, lớp học phần, đăng ký, điểm học phần, kết quả học kỳ, rèn luyện, điều kiện TN."""
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    CHAR, BigInteger, Boolean, CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, Base


class ThangDiem(Base):
    """Quy đổi điểm chữ ↔ hệ 10 ↔ hệ 4. tu/den/diem_4/dat NULL với I, X, R."""
    __tablename__ = "thang_diem"
    __table_args__ = CORE

    diem_chu: Mapped[str] = mapped_column(String(2), primary_key=True)
    tu: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    den: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    diem_4: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    dat: Mapped[bool | None] = mapped_column(Boolean)
    tinh_tb: Mapped[bool] = mapped_column(Boolean)
    mo_ta: Mapped[str] = mapped_column(String(150))


class LopHp(Base):
    """Lớp học phần. he_so là hệ số lớp khi tính học phí (lớp theo kế hoạch = 1,0)."""
    __tablename__ = "lop_hp"
    __table_args__ = (
        Index("ix_lop_hp_hk", "ma_hk"),
        CORE,
    )

    ma_lop: Mapped[str] = mapped_column(String(20), primary_key=True)
    ma_mon: Mapped[str] = mapped_column(String(10), ForeignKey("core.mon.ma_mon"))
    ma_hk: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"))
    theo_yeu_cau: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    si_so: Mapped[int | None] = mapped_column(SmallInteger)
    he_so: Mapped[Decimal] = mapped_column(Numeric(2, 1), default=1.0, server_default="1.0")
    # Giảng viên phụ trách và phòng học mặc định (phục vụ lịch học)
    ma_gv: Mapped[str | None] = mapped_column(String(10), ForeignKey("core.giang_vien.ma_gv"))
    phong: Mapped[str | None] = mapped_column(String(20))


class DangKy(Base):
    __tablename__ = "dang_ky"
    __table_args__ = (
        CheckConstraint("loai IN ('lan_dau', 'hoc_lai', 'cai_thien', 'hoc_doi')", name="ck_dang_ky_loai"),
        CheckConstraint("trang_thai IN ('dang_ky', 'da_huy')", name="ck_dang_ky_trang_thai"),
        Index("ix_dang_ky_lop", "ma_lop"),
        CORE,
    )

    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), primary_key=True)
    ma_lop: Mapped[str] = mapped_column(String(20), ForeignKey("core.lop_hp.ma_lop"), primary_key=True)
    ngay: Mapped[date]
    loai: Mapped[str] = mapped_column(String(10))
    trang_thai: Mapped[str] = mapped_column(String(10), default="dang_ky", server_default="dang_ky")


class DiemHp(Base):
    """Mỗi dòng = một lần học. Môn học lại có nhiều dòng.

    chinh_thuc = lần học được dùng tính TB tích lũy (điểm cao nhất); điểm xét HB chỉ lấy lan_hoc = 1.
    """
    __tablename__ = "diem_hp"
    __table_args__ = (
        CheckConstraint("lan_hoc >= 1", name="ck_diem_hp_lan_hoc"),
        CheckConstraint("diem_qt BETWEEN 0 AND 10", name="ck_diem_hp_qt"),
        CheckConstraint("diem_thi BETWEEN 0 AND 10", name="ck_diem_hp_thi"),
        CheckConstraint("diem_10 BETWEEN 0 AND 10", name="ck_diem_hp_10"),
        UniqueConstraint("ma_sv", "ma_mon", "lan_hoc", name="uq_diem_hp_lan"),
        Index("ix_diem_hp_sv_hk", "ma_sv", "ma_hk"),
        # Mỗi môn chỉ một lần học được đánh dấu chính thức
        Index("uq_diem_chinh_thuc", "ma_sv", "ma_mon", unique=True, postgresql_where="chinh_thuc"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    ma_mon: Mapped[str] = mapped_column(String(10), ForeignKey("core.mon.ma_mon"))
    # HK thực học (có thể là HK phụ)
    ma_hk: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"))
    ma_lop: Mapped[str | None] = mapped_column(String(20), ForeignKey("core.lop_hp.ma_lop"))  # NULL với điểm R
    lan_hoc: Mapped[int] = mapped_column(SmallInteger)
    diem_qt: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))  # điểm quá trình
    diem_thi: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    diem_10: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))  # điểm học phần hệ 10
    diem_chu: Mapped[str | None] = mapped_column(String(2), ForeignKey("core.thang_diem.diem_chu"))
    chinh_thuc: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class KetQuaHk(Base):
    """Kết quả chính thức theo HK chính (đã gộp HK phụ) — QCĐT Điều 10-11."""
    __tablename__ = "ket_qua_hk"
    __table_args__ = (
        CheckConstraint(
            "xep_loai IN ('xuat_sac', 'gioi', 'kha', 'trung_binh', 'yeu', 'kem')", name="ck_ket_qua_hk_xep_loai"
        ),
        CheckConstraint("nam_thu BETWEEN 1 AND 4", name="ck_ket_qua_hk_nam_thu"),
        CORE,
    )

    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), primary_key=True)
    ma_hk: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"), primary_key=True)
    tc_dk: Mapped[int] = mapped_column(SmallInteger)
    tc_dat: Mapped[int] = mapped_column(SmallInteger)
    tc_truot: Mapped[int] = mapped_column(SmallInteger)
    tb_hk: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))  # hệ 4
    tc_tich_luy: Mapped[int] = mapped_column(SmallInteger)
    tb_tich_luy: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))  # hệ 4
    xep_loai: Mapped[str | None] = mapped_column(String(12))
    nam_thu: Mapped[int | None] = mapped_column(SmallInteger)  # 4 = năm cuối
    canh_bao: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class RenLuyen(Base):
    """Điểm rèn luyện theo HK chính (đã áp trần do kỷ luật)."""
    __tablename__ = "ren_luyen"
    __table_args__ = (
        CheckConstraint("diem BETWEEN 0 AND 100", name="ck_ren_luyen_diem"),
        CheckConstraint(
            "xep_loai IN ('xuat_sac', 'tot', 'kha', 'trung_binh', 'yeu', 'kem')", name="ck_ren_luyen_xep_loai"
        ),
        CORE,
    )

    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), primary_key=True)
    ma_hk: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"), primary_key=True)
    diem: Mapped[int] = mapped_column(SmallInteger)
    xep_loai: Mapped[str] = mapped_column(String(12))


class DkTotNghiep(Base):
    """Điều kiện tốt nghiệp ngoài tín chỉ."""
    __tablename__ = "dk_tot_nghiep"
    __table_args__ = (
        CheckConstraint("loai IN ('ngoai_ngu', 'cntt', 'gdtc', 'gdqp')", name="ck_dk_tot_nghiep_loai"),
        CORE,
    )

    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), primary_key=True)
    loai: Mapped[str] = mapped_column(String(10), primary_key=True)
    dat: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    ngay_dat: Mapped[date | None]
    ghi_chu: Mapped[str | None] = mapped_column(String(200))  # VD 'IELTS 5.5'
