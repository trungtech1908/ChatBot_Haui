"""Học bổng: loại, mức theo năm học, học bổng sinh viên đã nhận."""
from datetime import date
from decimal import Decimal

from sqlalchemy import CHAR, BigInteger, CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, Base


class LoaiHb(Base):
    __tablename__ = "loai_hb"
    __table_args__ = (
        CheckConstraint("nhom IN ('haui', 'kkht', 'thac_si', 'tai_tro', 'ntb')", name="ck_loai_hb_nhom"),
        CheckConstraint("chu_ky IN ('hoc_ky', 'nam_hoc')", name="ck_loai_hb_chu_ky"),
        CORE,
    )

    ma_loai: Mapped[str] = mapped_column(String(15), primary_key=True)
    ten: Mapped[str] = mapped_column(String(150))
    nhom: Mapped[str] = mapped_column(String(10))
    chu_ky: Mapped[str] = mapped_column(String(10))
    van_ban: Mapped[str] = mapped_column(String(150))


class MucHb(Base):
    """Mức học bổng theo năm học: so_tien tuyệt đối hoặc ty_le học phí (1.000 = 100%)."""
    __tablename__ = "muc_hb"
    __table_args__ = (
        CheckConstraint("xep_loai IN ('xuat_sac', 'gioi', 'kha', 'chung')", name="ck_muc_hb_xep_loai"),
        CheckConstraint("so_tien IS NOT NULL OR ty_le IS NOT NULL", name="ck_muc_hb_gia_tri"),
        CORE,
    )

    ma_loai: Mapped[str] = mapped_column(String(15), ForeignKey("core.loai_hb.ma_loai"), primary_key=True)
    nam_hoc: Mapped[str] = mapped_column(CHAR(9), primary_key=True)
    xep_loai: Mapped[str] = mapped_column(String(10), primary_key=True, default="chung", server_default="chung")
    so_tien: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    ty_le: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    ghi_chu: Mapped[str | None] = mapped_column(String(200))


class HocBong(Base):
    """Học bổng sinh viên đã nhận. Xét theo học kỳ (ma_hk) hoặc năm học (nam_hoc)."""
    __tablename__ = "hoc_bong"
    __table_args__ = (
        CheckConstraint("xep_loai IN ('xuat_sac', 'gioi', 'kha')", name="ck_hoc_bong_xep_loai"),
        CheckConstraint("ma_hk IS NOT NULL OR nam_hoc IS NOT NULL", name="ck_hoc_bong_dot"),
        Index("ix_hoc_bong_sv", "ma_sv"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    ma_loai: Mapped[str] = mapped_column(String(15), ForeignKey("core.loai_hb.ma_loai"))
    ma_hk: Mapped[str | None] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"))
    nam_hoc: Mapped[str | None] = mapped_column(CHAR(9))
    xep_loai: Mapped[str | None] = mapped_column(String(10))
    dt_ntb: Mapped[str | None] = mapped_column(String(10))  # đối tượng HB Nguyễn Thanh Bình, VD '2.1.7'
    nha_tai_tro: Mapped[str | None] = mapped_column(String(150))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    so_qd: Mapped[str | None] = mapped_column(String(30))
    ngay_qd: Mapped[date | None]
