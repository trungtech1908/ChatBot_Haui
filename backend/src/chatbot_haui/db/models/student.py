from sqlalchemy import Boolean, Column, Numeric, Date, CHAR, VARCHAR, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from chatbot_haui.db.session import Base


# 1.bảng sinh viên (SINH_VIEN)
class SinhVien(Base):
    __tablename__ = 'sinhVien'

    maSV = Column(CHAR(10), primary_key=True, unique=True)
    hoTen = Column(VARCHAR(50))
    email=Column(CHAR(50)) 
    NgaySinh=Column(Date)
    soDT=Column(CHAR(10))
    diaChi=Column(VARCHAR(50))
    ngayTao=Column(DateTime)
    ngayCapNhat=Column(DateTime)
    maCT=Column(CHAR(10), ForeignKey('ctdt.maCT'))

    # Relationships One-to-One
    taiChinh = relationship("TaiChinh", back_populates="sinhVien_rel", uselist=False)
    doiTuong = relationship("DoiTuong", back_populates="sinhVien_rel", uselist=False)
    dieuKienTotNghiep = relationship("DieuKienTotNghiep", back_populates="sinhVien_rel", uselist=False)
    taiKhoan = relationship("TaiKhoan", back_populates="sinhVien_rel", uselist=False)

    # Relationships One-to-Many
    ketQuaMonHoc = relationship("KetQuaMonHoc", back_populates="sinhVien_rel")
    giaoDich = relationship("GiaoDich", back_populates="sinhVien_rel")
    lichThiSV = relationship("LichThiSV", back_populates="sinhVien_rel")
    ct_dt = relationship("CT_DT", back_populates="sinhVien")

    # Relationships to Junction Tables (One-to-Many to the junction table)
    lopHocDangKy = relationship("SinhVienLopHoc", back_populates="sinhVien_rel")
    thucTapRecords = relationship("ThucTap", back_populates="sinhVien_rel")


# 3.bảng đối tượng (ĐỐI_TƯỢNG)
class DoiTuong(Base):
    __tablename__= 'doiTuong' 
    maSV= Column(CHAR(10), ForeignKey('sinhVien.maSV'), primary_key=True, unique=True, nullable=False)
    ho_Ngheo=Column(Boolean, default=False)
    ho_Can_Ngheo=Column(Boolean, default=False)
    mo_Coi=Column(Boolean, default=False)
    khuyet_Tan=Column(Boolean, default=False)
    dan_Toc=Column(VARCHAR(20), default=False)
    quoc_Tich=Column(VARCHAR(30), default=False)

    sinhVien_rel = relationship("SinhVien", back_populates="doiTuong")


# 4.bảng điều kiện tốt nghiệp (ĐIỀU_KIỆN_TỐT_NGHIỆP)
class DieuKienTotNghiep(Base):
    __tablename__= 'dieuKienTotNghiep'
    maSV= Column(CHAR(10), ForeignKey('sinhVien.maSV'), primary_key=True, unique=True, nullable=False)
    tb_GPA=Column(Numeric(2,1), default=0)
    DKSoTC=Column(Boolean, default=False)
    DKTheChat=Column(Boolean, default=False)
    DKNgoaiNgu=Column(Boolean, default=False)
    DK_GDQP=Column(Boolean, default=False)
    sinhVien_rel = relationship("SinhVien", back_populates="dieuKienTotNghiep")


# 5.bảng tài khoản (TÀI_KHOẢN)
class TaiKhoan(Base):
    __tablename__= 'taiKhoan'
    tenTaiKhoan=Column(CHAR(50), primary_key=True, unique=True)
    matKhau=Column(VARCHAR(255))  # hash argon2
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'), nullable=False)
    sinhVien_rel = relationship("SinhVien", back_populates="taiKhoan")
