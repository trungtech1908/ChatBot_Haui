from sqlalchemy import Column, Integer, CHAR, VARCHAR, ForeignKey
from sqlalchemy.orm import relationship

from chatbot_haui.db.session import Base


# 22.bảng Doanh nghiệp (DOANH_NGHIỆP)
class DoanhNghiep(Base):
    __tablename__='doanhNghiep'
    maDN=Column(CHAR(10), primary_key=True)
    tenDN=Column(VARCHAR(50))
    diaChi=Column(VARCHAR(50))
    soDT=Column(CHAR(10))
    email=Column(CHAR(50))
    chuyenNganh=Column(VARCHAR(50))
    soLuongSV=Column(Integer)
    
    thucTapRecords = relationship("ThucTap", back_populates="doanhNghiep_rel")


# 23.bảng thực tập (THỰC_TẬP - Junction Table 3 chiều)
class ThucTap(Base):
    __tablename__='thucTap'
    maDN=Column(CHAR(10),ForeignKey('doanhNghiep.maDN'), primary_key=True)
    maGV=Column(CHAR(10),ForeignKey('giangVien.maGV'), primary_key=True)
    maSV=Column(CHAR(10),ForeignKey('sinhVien.maSV'), primary_key=True)
    viTriTT=Column(VARCHAR(50))

    doanhNghiep_rel = relationship("DoanhNghiep", back_populates="thucTapRecords")
    giangVien_rel = relationship("GiangVien", back_populates="thucTapRecords")
    sinhVien_rel = relationship("SinhVien", back_populates="thucTapRecords")
