"""Học phí và tài chính.

Học phí 1 lớp = n_hp × he_so_lop × don_gia
  n_hp = tc_lt × 1,0 + tc_dac_thu × 1,5 + tc_th × 2,5
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, BigInteger, CheckConstraint, ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from chatbot_haui.db.session import CORE, Base


class HeSoTc(Base):
    """Hệ số quy đổi tín chỉ học phí."""
    __tablename__ = "he_so_tc"
    __table_args__ = (
        CheckConstraint("loai_tc IN ('lt', 'dac_thu', 'th')", name="ck_he_so_tc_loai"),
        CORE,
    )

    loai_tc: Mapped[str] = mapped_column(String(10), primary_key=True)
    he_so: Mapped[Decimal] = mapped_column(Numeric(2, 1))
    mo_ta: Mapped[str] = mapped_column(String(200))


class DonGia(Base):
    """Đơn giá 1 TC học phí theo năm học, bậc, khóa, loại CTĐT."""
    __tablename__ = "don_gia"
    __table_args__ = (
        CheckConstraint("bac IN ('dai_hoc', 'ky_su', 'cao_dang')", name="ck_don_gia_bac"),
        CheckConstraint("hinh_thuc IN ('chinh_quy', 'vlvh', 'tu_xa')", name="ck_don_gia_hinh_thuc"),
        CheckConstraint("loai_ctdt IN ('dai_tra', 'tieng_anh', 'tat_ca')", name="ck_don_gia_loai_ctdt"),
        CheckConstraint("nhom_mon IN ('tat_ca', 'gdtc_gdqp')", name="ck_don_gia_nhom_mon"),
        CheckConstraint("don_vi IN ('tc', 'thang', 'nam')", name="ck_don_gia_don_vi"),
        CORE,
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nam_hoc: Mapped[str] = mapped_column(CHAR(9))
    bac: Mapped[str] = mapped_column(String(10))
    khoa_tu: Mapped[int]  # áp dụng cho khóa [khoa_tu, khoa_den]
    khoa_den: Mapped[int]
    hinh_thuc: Mapped[str] = mapped_column(String(10))
    loai_ctdt: Mapped[str] = mapped_column(String(10))
    nhom_mon: Mapped[str] = mapped_column(String(10), default="tat_ca", server_default="tat_ca")
    don_gia: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    don_vi: Mapped[str] = mapped_column(String(10))
    so_qd: Mapped[str] = mapped_column(String(30))


class KhoanThu(Base):
    """Khoản thu ngoài học phí: BHYT, BH thân thể, khám sức khỏe, ..."""
    __tablename__ = "khoan_thu"
    __table_args__ = (
        CheckConstraint(
            "bac IN ('dai_hoc', 'ky_su', 'cao_dang', 'lien_thong', 'tat_ca')", name="ck_khoan_thu_bac"
        ),
        CORE,
    )

    ma_kt: Mapped[str] = mapped_column(String(20), primary_key=True)
    ten: Mapped[str] = mapped_column(String(150))
    nam_hoc: Mapped[str | None] = mapped_column(CHAR(9))
    bac: Mapped[str] = mapped_column(String(10))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    chu_ky: Mapped[str] = mapped_column(String(30))  # '15 tháng', '4 năm học', 'khóa học', 'lượt'
    tu_ngay: Mapped[date | None]
    den_ngay: Mapped[date | None]
    ghi_chu: Mapped[str | None] = mapped_column(String(300))
    so_qd: Mapped[str | None] = mapped_column(String(30))


class PhaiThu(Base):
    """Khoản SV phải nộp. Dòng học phí lưu lại n_hp, he_so_lop, don_gia lúc tính để giải thích được con số."""
    __tablename__ = "phai_thu"
    __table_args__ = (
        CheckConstraint("loai IN ('hoc_phi', 'khoan_thu', 'phi_phat', 'khac')", name="ck_phai_thu_loai"),
        CheckConstraint("so_tien >= 0", name="ck_phai_thu_so_tien"),
        CheckConstraint("trang_thai IN ('hieu_luc', 'da_huy')", name="ck_phai_thu_trang_thai"),
        CheckConstraint("loai <> 'hoc_phi' OR ma_lop IS NOT NULL", name="ck_phai_thu_hoc_phi_co_lop"),
        Index("ix_phai_thu_sv_hk", "ma_sv", "ma_hk"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    ma_hk: Mapped[str] = mapped_column(CHAR(5), ForeignKey("core.hoc_ky.ma_hk"))
    loai: Mapped[str] = mapped_column(String(10))
    ma_lop: Mapped[str | None] = mapped_column(String(20), ForeignKey("core.lop_hp.ma_lop"))  # với học phí
    ma_kt: Mapped[str | None] = mapped_column(String(20), ForeignKey("core.khoan_thu.ma_kt"))  # với khoản thu
    n_hp: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))  # số TC học phí
    he_so_lop: Mapped[Decimal | None] = mapped_column(Numeric(2, 1))
    don_gia: Mapped[Decimal | None] = mapped_column(Numeric(12, 0))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    han_nop: Mapped[date | None]
    trang_thai: Mapped[str] = mapped_column(String(10), default="hieu_luc", server_default="hieu_luc")


class GiaoDich(Base):
    """Dòng tiền vào/ra tài khoản cá nhân của SV trên hệ thống ĐH điện tử.

    Số dư và công nợ được tính từ sổ cái này, không lưu sẵn.
    """
    __tablename__ = "giao_dich"
    __table_args__ = (
        CheckConstraint(
            "loai IN ('nap_tien', 'rut_tien', 'thanh_toan', 'hoan_tien', 'nhan_hb', 'nhan_mghp', 'nhan_ho_tro')",
            name="ck_giao_dich_loai",
        ),
        CheckConstraint("chieu IN ('vao', 'ra')", name="ck_giao_dich_chieu"),
        CheckConstraint("so_tien > 0", name="ck_giao_dich_so_tien"),
        CheckConstraint("trang_thai IN ('thanh_cong', 'that_bai', 'dang_xu_ly')", name="ck_giao_dich_trang_thai"),
        Index("ix_giao_dich_sv", "ma_sv", "thoi_gian"),
        CORE,
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ma_sv: Mapped[str] = mapped_column(String(12), ForeignKey("core.sinh_vien.ma_sv"))
    thoi_gian: Mapped[datetime]
    loai: Mapped[str] = mapped_column(String(15))
    chieu: Mapped[str] = mapped_column(String(3))
    so_tien: Mapped[Decimal] = mapped_column(Numeric(12, 0))
    ma_phai_thu: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("core.phai_thu.id"))
    ma_hb: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("core.hoc_bong.id"))
    trang_thai: Mapped[str] = mapped_column(String(12))
    kenh: Mapped[str | None] = mapped_column(String(20))  # 'ngan_hang', 'vi_dien_tu', 'he_thong'
    ghi_chu: Mapped[str | None] = mapped_column(String(300))
