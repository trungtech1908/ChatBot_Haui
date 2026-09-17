from sqlalchemy import Boolean, Column, Numeric, Date, Text, Float, CHAR, VARCHAR, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from chatbot_haui.db.session import Base


# 2.bảng tài chính (TÀI_CHÍNH)
class TaiChinh(Base):
    __tablename__= 'taiChinh'
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'), primary_key=True, unique=True, nullable=False)
    soDu=Column(Numeric(12,0), default=0)
    no=Column(Numeric(12,0), default=0)
    duocGiam=Column(Float, default=0)
    hocBong=Column(Numeric(12,0), default=0)
    sinhVien_rel = relationship("SinhVien", back_populates="taiChinh")


# 24.bảng Khoảng thu khác (KHOẢNG_THU_KHÁC)
class KhoangThuKhac(Base):
    __tablename__='khoangThuKhac'
    maKT=Column(CHAR(10), primary_key=True)
    tenKT=Column(VARCHAR(50))
    gia=Column(Numeric(10,0))
    ngayBD=Column(Date)
    han=Column(Date)
    giaChu=Column(Text)
    
    giaoDich = relationship("GiaoDich", back_populates="khoangThuKhac_rel")


# 25.bảng giao dịch (GIAO_DỊCH)
class GiaoDich(Base):
    __tablename__= 'giaoDich'
    maGD=Column(CHAR(10), primary_key=True)
    tenGD=Column(VARCHAR(50))
    ThanhTien=Column(Numeric(10,0))
    Cong_Tru=Column(Boolean, default=True)
    GhiChu=Column(Text)
    maMH=Column(CHAR(10),ForeignKey('monHoc.maMH'))
    maKT=Column(CHAR(10),ForeignKey('khoangThuKhac.maKT'))
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'))
    
    monHoc_rel = relationship("MonHoc", back_populates="giaoDich")
    khoangThuKhac_rel = relationship("KhoangThuKhac", back_populates="giaoDich")
    sinhVien_rel = relationship("SinhVien", back_populates="giaoDich")
    lichSuGiaoDich = relationship("LSGD", back_populates="giaoDich_rel")


# 26.bảng lịch sử giao dịch (LSGD)
class LSGD(Base):
    __tablename__='lsgd'
    maLGD=Column(CHAR(10), primary_key=True)
    maGD=Column(CHAR(10),ForeignKey('giaoDich.maGD'))
    ThoiGian=Column(DateTime)
    TrangThai=Column(Boolean)

    giaoDich_rel = relationship("GiaoDich", back_populates="lichSuGiaoDich")
