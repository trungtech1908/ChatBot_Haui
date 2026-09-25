"""Đối tượng và chính sách: miễn giảm học phí, hỗ trợ chi phí học tập, mức trần, tham số."""
from datetime import date
from decimal import Decimal

from sqlalchemy import CHAR, BigInteger, CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, Base


class DoiTuong(Base):
    """Danh mục: ho_ngheo, khuyet_tat, mo_coi, dtts, ..."""
    __tablename__ = "doi_tuong"
    __table_args__ = CORE

    ma_dt: Mapped[str] = mapped_column(String(30), primary_key=True)
    ten: Mapped[str] = mapped_column(String(200))


class SvDoiTuong(Base):
    """SV thuộc đối tượng nào, có thời hạn (hộ nghèo chỉ hiệu lực trong năm được công nhận)."""
    __tablename__ = "sv_doi_tuong"
    __table_args__ = (
        CheckConstraint("trang_thai IN ('cho_duyet', 'da_duyet', 'tu_choi')", name="ck_sv_doi_tuong_trang_thai"),
        CORE,
    )

    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"), primary_key=True)
    ma_dt: Mapped[str] = mapped_column(String(30), ForeignKey("core.doi_tuong.ma_dt"), primary_key=True)
    tu_ngay: Mapped[date] = mapped_column(primary_key=True)
    den_ngay: Mapped[date | None]
    trang_thai: Mapped[str] = mapped_column(String(10), default="cho_duyet", server_default="cho_duyet")


class ChinhSach(Base):
    """Danh mục chính sách. co_so cho biết ty_le tính theo mức trần, lương cơ sở hay học phí."""
    __tablename__ = "chinh_sach"
    __table_args__ = (
        CheckConstraint(
            "nhom IN ('mien_hp', 'giam_hp', 'ho_tro_cp', 'noi_tru', 'ho_tro_ht', 'ho_tro_haui')",
            name="ck_chinh_sach_nhom",
        ),
        CheckConstraint("co_so IN ('muc_tran', 'luong_co_so', 'hoc_phi', 'khac')", name="ck_chinh_sach_co_so"),
        CORE,
    )

    ma_cs: Mapped[str] = mapped_column(String(20), primary_key=True)
    ten: Mapped[str] = mapped_column(String(200))
    nhom: Mapped[str] = mapped_column(String(15))
    ty_le: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    co_so: Mapped[str] = mapped_column(String(15))
    so_thang: Mapped[int | None] = mapped_column(SmallInteger)  # số tháng hưởng/năm
    can_cu: Mapped[str] = mapped_column(String(150))


class SvChinhSach(Base):
    """Chính sách SV được hưởng, có thời hạn và số quyết định."""
    __tablename__ = "sv_chinh_sach"
    __table_args__ = (
        CheckConstraint("trang_thai IN ('dang_huong', 'tam_dung', 'ket_thuc')", name="ck_sv_chinh_sach_trang_thai"),
        Index("ix_sv_cs_sv", "ma_sv"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    ma_cs: Mapped[str] = mapped_column(String(20), ForeignKey("core.chinh_sach.ma_cs"))
    ma_dt: Mapped[str | None] = mapped_column(String(30), ForeignKey("core.doi_tuong.ma_dt"))
    tu_ngay: Mapped[date]
    den_ngay: Mapped[date | None]
    so_qd: Mapped[str | None] = mapped_column(String(30))
    trang_thai: Mapped[str] = mapped_column(String(10), default="dang_huong", server_default="dang_huong")


class MucTran(Base):
    """Mức trần miễn giảm học phí theo khối ngành, năm học (VND/SV/tháng)."""
    __tablename__ = "muc_tran"
    __table_args__ = CORE

    ma_khoi: Mapped[str] = mapped_column(String(20), ForeignKey("core.khoi_nganh.ma_khoi"), primary_key=True)
    nam_hoc: Mapped[str] = mapped_column(CHAR(9), primary_key=True)
    muc_thang: Mapped[Decimal] = mapped_column(Numeric(12, 0))


class ThamSo(Base):
    """Tham số theo thời gian: lương cơ sở, ..."""
    __tablename__ = "tham_so"
    __table_args__ = CORE

    ma: Mapped[str] = mapped_column(String(30), primary_key=True)
    tu_ngay: Mapped[date] = mapped_column(primary_key=True)
    gia_tri: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    den_ngay: Mapped[date | None]
    ghi_chu: Mapped[str | None] = mapped_column(String(200))
