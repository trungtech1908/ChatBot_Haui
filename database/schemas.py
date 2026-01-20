# schemas.py (Cần có tất cả các models này)

from pydantic import BaseModel, RootModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime

# Model cơ sở
class BaseCreate(BaseModel):
    pass
# -----------------------------------------------------------------
# 1-5: Bảng chính và Bảng phụ thuộc SinhVien
# -----------------------------------------------------------------
class SinhVienCreate(BaseCreate):
    maSV: str; hoTen: Optional[str] = None; email: Optional[str] = None; NgaySinh: Optional[date] = None; soDT: Optional[str] = None; diaChi: Optional[str] = None; maCT: str
class TaiChinhCreate(BaseCreate):
    maSV: str; soDu: Optional[int] = 0; no: Optional[int] = 0; duocGiam: Optional[float] = 0.0; hocBong: Optional[int] = 0
class DoiTuongCreate(BaseCreate):
    maSV: str; ho_Ngheo: Optional[bool] = False; ho_Can_Ngheo: Optional[bool] = False; mo_Coi: Optional[bool] = False; khuyet_Tan: Optional[bool] = False; dan_Toc: Optional[str] = None; quoc_Tich: Optional[str] = None
class DieuKienTotNghiepCreate(BaseCreate):
    maSV: str; tb_GPA: Optional[float] = 0.0; DKSoTC: Optional[bool] = False; DKTheChat: Optional[bool] = False; DKNgoaiNgu: Optional[bool] = False; DK_GDQP: Optional[bool] = False
class TaiKhoanCreate(BaseCreate):
    tenTaiKhoan: str; matKhau: Optional[str] = None; maSV: str
# -----------------------------------------------------------------
# 6-12: Bảng Khoa, CTDT, Môn học
# -----------------------------------------------------------------
class KhoaCreate(BaseCreate):
    maKhoa: str; tenKhoa: Optional[str] = None
class CT_DTCreate(BaseCreate):
    maCT: str; nganhHoc:str; khoaHoc:str; soTC_YeuCau: Optional[int] = None; soMon: Optional[int] = None; maKhoa: Optional[str] = None
class MonHocCreate(BaseCreate):
    maMH: str; tenMonHoc: str; soTC: int; heSoTC: int; moTa: Optional[str] = None; trongSo_tx1: float; trongSo_tx2: float; trongSo_giuaKy: float; trongSo_BaiThi: float; giaTC: int; gia: int; ngayPhatHanh: date; maKhoa: str
class NhomMHCreate(BaseCreate):
    maNhom: str; TenNhom: Optional[str] = None; loaiNhom: Optional[str] = None; soTC_YC: Optional[int] = None
class CT_CTDTCreate(BaseCreate): # Junction
    maCT:str; maNhom: str
class CT_NMHCreate(BaseCreate): # Junction
    maNhom: str; maMH: str; ky:int
class TQMHCreate(BaseCreate): # Junction
    maMH: str; maTQ: str
# -----------------------------------------------------------------
# 13-18: Bảng Giảng Viên, Lớp học, Lịch, KQ học tập
# -----------------------------------------------------------------
class GiangVienCreate(BaseCreate):
    maGV: str; hoTen: Optional[str] = None; email: Optional[str] = None; NgaySinh: Optional[date] = None; soDT: Optional[str] = None; diaChi: Optional[str] = None; maKhoa: Optional[str] = None
class LopHocCreate(BaseCreate):
    maLH: str; ngayBD: Optional[date] = None; ngayKT: Optional[date] = None; soPhong: Optional[int] = None; hanHuy: Optional[date] = None; soTuanHoc: Optional[int] = None; SisoThucTe: Optional[int] = None; SisoToiDa: Optional[int] = None; maMH: Optional[str] = None; maGV: Optional[str] = None
class KetQuaMonHocCreate(BaseCreate):
    maKQ: str; tx1: Optional[float] = 0.0; tx2: Optional[float] = 0.0; giuaKy: Optional[float] = 0.0; BaiThi: Optional[float] = 0.0; diemGPA: Optional[float] = 0.0; diemChu: Optional[str] = None; hocLai: Optional[bool] = False; maKQHY: Optional[str] = None; maMH: Optional[str] = None; maSV: Optional[str] = None
class KetQuaHocKyCreate(BaseCreate):
    maKQHY: str; hocKy: Optional[int] = None; TongTC: Optional[int] = None; diemTBC: Optional[float] = None
class LichHocCreate(BaseCreate):
    maDOW: str; tietHoc: Optional[str] = None; thu: Optional[int] = None; tuanHoc: Optional[int] = None; maLH: Optional[str] = None
class LichThiCreate(BaseCreate):
    maLT: str; soPhong: Optional[int] = None; gioBD: Optional[datetime] = None; gioKT: Optional[datetime] = None; hinhThucThi: Optional[str] = None
# -----------------------------------------------------------------
# 18-23: Bảng Junction và Thực Tập
# -----------------------------------------------------------------
class SinhVienLopHocCreate(BaseCreate): # Junction
    maSV: str; maLH: str; NgayDK: Optional[date] = None; TrangThai_DK: Optional[bool] = None
class LichThiSVCreate(BaseCreate):
    soBD: int; maSV: Optional[str] = None; maLT: Optional[str] = None; viTri: Optional[str] = None; dieuKienThi: Optional[bool] = None
class PhuTrachCreate(BaseCreate): # Junction
    maMH: str; maGV: str
class DoanhNghiepCreate(BaseCreate):
    maDN: str; tenDN: Optional[str] = None; diaChi: Optional[str] = None; soDT: Optional[str] = None; email: Optional[str] = None; chuyenNganh: Optional[str] = None; soLuongSV: Optional[int] = None
class ThucTapCreate(BaseCreate): # Junction 3 chiều
    maDN: str; maGV: str; maSV: str; viTriTT: Optional[str] = None
# -----------------------------------------------------------------
# 24-26: Bảng Giao dịch
# -----------------------------------------------------------------
class KhoangThuKhacCreate(BaseCreate):
    maKT: str; tenKT: Optional[str] = None; gia: Optional[int] = None; ngayBD: Optional[date] = None; han: Optional[date] = None; giaChu: Optional[str] = None
class GiaoDichCreate(BaseCreate):
    maGD: str; tenGD: Optional[str] = None; ThanhTien: Optional[int] = None; Cong_Tru: Optional[bool] = True; GhiChu: Optional[str] = None; maMH: Optional[str] = None; maKT: Optional[str] = None; maSV: Optional[str] = None
class LSGDCreate(BaseCreate):
    maLGD: str; maGD: Optional[str] = None; ThoiGian: Optional[datetime] = None; TrangThai: Optional[bool] = None

# --- Root Models (Payload) cho tất cả ---
class GenericPayload(RootModel):
    root: List[BaseCreate] # Sẽ được thay thế bằng model cụ thể khi chạy