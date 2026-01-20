from sqlalchemy import (
    Boolean, Column, Integer, Numeric, Date, Text, Float, CHAR, VARCHAR, 
    ForeignKey, Time, DateTime, Index, UniqueConstraint
) 
from database.database import Base
from sqlalchemy.orm import relationship

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

# 2.bảng tài chính (TÀI_CHÍNH)
class TaiChinh(Base):
    __tablename__= 'taiChinh'
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'), primary_key=True, unique=True, nullable=False)
    soDu=Column(Numeric(12,0), default=0)
    no=Column(Numeric(12,0), default=0)
    duocGiam=Column(Float, default=0)
    hocBong=Column(Numeric(12,0), default=0)
    sinhVien_rel = relationship("SinhVien", back_populates="taiChinh")

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
    matKhau=Column(VARCHAR(25))
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'), nullable=False)
    sinhVien_rel = relationship("SinhVien", back_populates="taiKhoan")

# ---
# 6.bảng khoa (KHOA)
class Khoa(Base):
    __tablename__= 'khoa'
    maKhoa=Column(CHAR(10), primary_key=True, unique=True)
    tenKhoa=Column(VARCHAR(50))
    chuongTrinhDaoTao = relationship("CT_DT", back_populates="khoa_rel")
    giangVien = relationship("GiangVien", back_populates="khoa_rel")
    monHoc=relationship('MonHoc', back_populates='khoa_rel')

# 7.bảng chương trình đào tạo (CHƯƠNG_TRÌNH_ĐÀO_TẠO)
class CT_DT(Base):
    __tablename__='ctdt'
    maCT=Column(CHAR(10), primary_key=True, unique=True)
    nganhHoc=Column(VARCHAR(50))
    khoaHoc=Column(VARCHAR(10))
    soTC_YeuCau=Column(Integer)
    soMon=Column(Integer)
    maKhoa=Column(CHAR(10), ForeignKey('khoa.maKhoa'))
    
    khoa_rel = relationship("Khoa", back_populates="chuongTrinhDaoTao")
    ct_ctdt = relationship("CT_CTDT", back_populates="ct_dt")
    sinhVien = relationship("SinhVien", back_populates="ct_dt")


# ---
# 8.bảng môn học (MÔN_HỌC)
class MonHoc(Base):
    __tablename__ = 'monHoc'
    maMH=Column(CHAR(10), primary_key=True) 
    tenMonHoc=Column(VARCHAR(50), nullable=False)
    soTC=Column(Integer, nullable=False)
    heSoTC=Column(Integer, nullable=False)
    moTa=Column(Text)
    trongSo_tx1=Column(Float, nullable=False)
    trongSo_tx2=Column(Float, nullable=False)
    trongSo_giuaKy=Column(Float, nullable=False)
    trongSo_BaiThi=Column(Float, nullable=False)
    giaTC=Column(Numeric(10,0), nullable=False)
    gia=Column(Numeric(10,0), nullable=False)
    ngayPhatHanh=Column(Date, nullable=False)

    maKhoa=Column(CHAR(10), ForeignKey('khoa.maKhoa'))

    # Relationships One-to-Many
    lopHoc = relationship("LopHoc", back_populates="monHoc_rel")
    ketQuaMonHoc = relationship("KetQuaMonHoc", back_populates="monHoc_rel")
    giaoDich = relationship("GiaoDich", back_populates="monHoc_rel")
    khoa_rel = relationship("Khoa", back_populates="monHoc")

    # Relationships to Junction Tables (One-to-Many to the junction table)
    ctdtRecords = relationship("CT_NMH", back_populates="monHoc_rel")
    phuTrachRecords = relationship("PhuTrach", back_populates="monHoc_rel")
    
    # Quan hệ tự tham chiếu (Tiên quyết)
    # 1. monTienQuyet: Môn học này cần Môn nào làm tiên quyết? (maMH là môn BỊ TQ)
    monTienQuyet = relationship(
        "MonHoc",
        secondary="tienQuyetMonHoc",
        primaryjoin=lambda: MonHoc.maMH == TQMH.maMH,   
        secondaryjoin=lambda: MonHoc.maMH == TQMH.maTQ,
        backref="monYeuCauTienQuyet" # Các môn mà môn hiện tại LÀ tiên quyết
    )

# 9.bảng nhóm môn học (NHÓM_MÔN_HỌC)
class NhomMH(Base):
    __tablename__='nhomMH'
    maNhom=Column(CHAR(20), primary_key=True)
    TenNhom=Column(VARCHAR(50))
    loaiNhom=Column(VARCHAR(20))
    soTC_YC=Column(Integer)
    
    ct_nmh = relationship("CT_NMH", back_populates="nhomMH")
    ct_ctdt=relationship("CT_CTDT", back_populates="nhomMH")

# 10.bảng chi tiết chương trình đào tạo (CT_CTDT - Junction Table)
class CT_CTDT(Base):
    __tablename__= 'ct_ctdt'
    maCT=Column(CHAR(10), ForeignKey('ctdt.maCT'), primary_key=True)
    maNhom=Column(CHAR(20), ForeignKey('nhomMH.maNhom'), primary_key=True)

    ct_dt = relationship("CT_DT", back_populates="ct_ctdt")
    nhomMH=relationship("NhomMH", back_populates="ct_ctdt")

# 11.bảng chi tiết nhóm môn học (CT_CTDT - Junction Table)
class CT_NMH(Base):
    __tablename__= 'ct_nmh'
    maNhom=Column(CHAR(20), ForeignKey('nhomMH.maNhom'), primary_key=True)
    maMH=Column(CHAR(10), ForeignKey('monHoc.maMH'), primary_key=True)
    ky=Column(Integer)

    monHoc_rel = relationship("MonHoc", back_populates="ctdtRecords")
    nhomMH=relationship("NhomMH", back_populates="ct_nmh")
    
    
# 12.bảng tiên quyết môn học (TQMH - Junction Table)
class TQMH(Base):
    __tablename__='tienQuyetMonHoc'
    maMH=Column(CHAR(10), ForeignKey('monHoc.maMH'), primary_key=True)
    maTQ=Column(CHAR(10), ForeignKey('monHoc.maMH'), primary_key=True)

# ---
# 13.bảng giảng viên (GIẢNG_VIÊN)
class GiangVien(Base):
    __tablename__ = 'giangVien'
    maGV=Column(CHAR(10), primary_key=True)
    hoTen = Column(VARCHAR(50))
    email=Column(CHAR(50)) 
    NgaySinh=Column(Date)
    soDT=Column(CHAR(10))
    diaChi=Column(VARCHAR(50))
    maKhoa=Column(CHAR(10),ForeignKey('khoa.maKhoa'))
    
    khoa_rel = relationship("Khoa", back_populates="giangVien")
    lopHocPhuTrach = relationship("LopHoc", back_populates="giangVien_rel")
    
    # Relationships to Junction Tables (One-to-Many to the junction table)
    phuTrachRecords = relationship("PhuTrach", back_populates="giangVien_rel")
    thucTapRecords = relationship("ThucTap", back_populates="giangVien_rel")

# 14.bảng lớp học (LỚP_HỌC)
class LopHoc(Base):
    __tablename__= 'lopHoc'
    maLH=Column(CHAR(10), primary_key=True)
    ngayBD=Column(Date)
    ngayKT=Column(Date)
    soPhong=Column(Integer)
    hanHuy=Column(Date)
    soTuanHoc=Column(Integer)
    SisoThucTe=Column(Integer)
    SisoToiDa=Column(Integer)
    maMH=Column(CHAR(10),ForeignKey('monHoc.maMH'))
    maGV=Column(CHAR(10),ForeignKey('giangVien.maGV'))
    
    monHoc_rel = relationship("MonHoc", back_populates="lopHoc")
    giangVien_rel = relationship("GiangVien", back_populates="lopHocPhuTrach")
    lichHoc = relationship("LichHoc", back_populates="lopHoc_rel")
    
    # Relationships to Junction Tables (One-to-Many to the junction table)
    sinhVienDangKy = relationship("SinhVienLopHoc", back_populates="lopHoc_rel")

# 15.bảng kết quả môn học (KẾT_QUẢ_MÔN_HỌC)
class KetQuaMonHoc(Base):
    __tablename__= 'ketQuaMonHoc'
    maKQ=Column(CHAR(10), primary_key=True)
    tx1=Column(Numeric(2,1), default=0)
    tx2=Column(Numeric(2,1), default=0)
    giuaKy=Column(Numeric(2,1), default=0)
    BaiThi=Column(Numeric(2,1), default=0)
    diemGPA=Column(Numeric(2,1), default=0)
    diemChu=Column(CHAR(2))
    hocLai=Column(Boolean, default=False)
    maKQHY=Column(CHAR(10), ForeignKey('ketQuaHocKy.maKQHY'))
    maMH=Column(CHAR(10), ForeignKey('monHoc.maMH'))
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'))

    ketQuaHocKy_rel = relationship("KetQuaHocKy", back_populates="ketQuaMonHoc")
    monHoc_rel = relationship("MonHoc", back_populates="ketQuaMonHoc")
    sinhVien_rel = relationship("SinhVien", back_populates="ketQuaMonHoc")

# 16.bảng kết quả học kỳ (KẾT_QUẢ_HỌC_KỲ)
class KetQuaHocKy(Base):
    __tablename__='ketQuaHocKy'
    maKQHY=Column(CHAR(10),primary_key=True)
    hocKy=Column(Integer)
    TongTC=Column(Integer)
    diemTBC=Column(Numeric(2,1))
    
    ketQuaMonHoc = relationship("KetQuaMonHoc", back_populates="ketQuaHocKy_rel")

# 17.bảng lịch học (LỊCH_HỌC)
class LichHoc(Base):
    __tablename__='lichHoc'
    maDOW=Column(CHAR(10), primary_key=True)
    tietHoc=Column(VARCHAR(20))
    thu=Column(Integer)
    tuanHoc=Column(Integer)
    maLH=Column(CHAR(10), ForeignKey('lopHoc.maLH'))
    
    lopHoc_rel = relationship("LopHoc", back_populates="lichHoc")

# 18.bảng lịch thi (LỊCH_THI)
class LichThi(Base):
    __tablename__='lichThi'
    maLT=Column(CHAR(10), primary_key=True)
    soPhong=Column(Integer)
    gioBD=Column(DateTime)
    gioKT=Column(DateTime)
    hinhThucThi=Column(VARCHAR(20))
    
    chiTietThi = relationship("LichThiSV", back_populates="lichThi_rel")

# 19.bảng sinh viên lớp học (SINH_VIÊN_LỚP_HỌC - Junction Table)
class SinhVienLopHoc(Base):
    __tablename__='sinhVienLopHoc'
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'), primary_key=True)
    maLH=Column(CHAR(10),ForeignKey('lopHoc.maLH'), primary_key=True)
    NgayDK=Column(Date)
    TrangThai_DK=Column(Boolean)

    sinhVien_rel = relationship("SinhVien", back_populates="lopHocDangKy")
    lopHoc_rel = relationship("LopHoc", back_populates="sinhVienDangKy")


# 20.bảng chi tiết lịch thi (LỊCH_THI_SV)
class LichThiSV(Base):
    __tablename__='lichThiSV'
    soBD=Column(Integer, primary_key=True)
    maSV=Column(CHAR(10), ForeignKey('sinhVien.maSV'))
    maLT=Column(CHAR(10), ForeignKey('lichThi.maLT'))
    viTri=Column(CHAR(5))
    dieuKienThi=Column(Boolean)

    sinhVien_rel = relationship("SinhVien", back_populates="lichThiSV")
    lichThi_rel = relationship("LichThi", back_populates="chiTietThi")

# 21.bảng phụ trách (PHỤ_TRÁCH - Junction Table)
class PhuTrach(Base):
    __tablename__='phuTrach'
    maMH=Column(CHAR(10),ForeignKey('monHoc.maMH'), primary_key=True)
    maGV=Column(CHAR(10),ForeignKey('giangVien.maGV'), primary_key=True)

    monHoc_rel = relationship("MonHoc", back_populates="phuTrachRecords")
    giangVien_rel = relationship("GiangVien", back_populates="phuTrachRecords")

# ---
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

# ---
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