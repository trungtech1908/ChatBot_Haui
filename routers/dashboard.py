from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload, subqueryload
import database.models as models
from database.database import get_db
import json
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")
# --- THÊM ĐOẠN CODE NÀY VÀO DƯỚI DÒNG KHAI BÁO TEMPLATES ---

def custom_sort_curriculum(ct_ctdt_list):
    """
    Hàm sắp xếp thứ tự ưu tiên hiển thị nhóm môn học
    1. Chính trị (G_CTPL)
    2. KHCB (_KHCB)
    3. Ngoại ngữ (G_NN)
    4. Thể chất (G_GDTC)
    5. Cơ sở ngành (_CS)
    6. Chuyên ngành (_CN)
    7. Tự chọn (_TC)
    8. Thực tập (_TTKL)
    """
    def sort_key(item):
        ma = item.maNhom
        if "G_CTPL" in ma: return 1
        if "KHCB" in ma: return 2
        if "G_NN" in ma: return 3
        if "G_GDTC" in ma: return 4
        if "_CS" in ma: return 5
        if "_CN" in ma: return 6
        if "_TC" in ma: return 7
        if "_TTKL" in ma: return 8
        return 9 # Các nhóm khác xếp cuối
        
    if not ct_ctdt_list:
        return []
    
    return sorted(ct_ctdt_list, key=sort_key)

# Đăng ký filter này với Jinja2 để dùng trong HTML
templates.env.filters['sort_nhom_mh'] = custom_sort_curriculum

CHAT_FILE = "json/chat_data.json"

@router.get("/welcome", response_class=HTMLResponse, name="welcome_dashboard")
def welcome_dashboard(request: Request, username: str, db: Session = Depends(get_db)): 
    sinh_vien_info = None
    error_data = None
    
    try:
        tai_khoan = db.query(models.TaiKhoan.maSV).filter(models.TaiKhoan.tenTaiKhoan == username).first()
        if not tai_khoan:
            error_data = "Không tìm thấy tài khoản."
        else:
            ma_sv = tai_khoan.maSV
            
            # Truy vấn phức tạp lấy toàn bộ dữ liệu
            sinh_vien_info = db.query(models.SinhVien).options(
                joinedload(models.SinhVien.taiChinh),
                joinedload(models.SinhVien.doiTuong),
                joinedload(models.SinhVien.dieuKienTotNghiep),
                joinedload(models.SinhVien.taiKhoan), 
                subqueryload(models.SinhVien.ketQuaMonHoc).options(
                    joinedload(models.KetQuaMonHoc.monHoc_rel), 
                    joinedload(models.KetQuaMonHoc.ketQuaHocKy_rel)
                ),
                subqueryload(models.SinhVien.giaoDich).joinedload(models.GiaoDich.lichSuGiaoDich),
                subqueryload(models.SinhVien.lichThiSV).joinedload(models.LichThiSV.lichThi_rel),
                subqueryload(models.SinhVien.thucTapRecords).options(
                    joinedload(models.ThucTap.doanhNghiep_rel), 
                    joinedload(models.ThucTap.giangVien_rel)
                ),
                subqueryload(models.SinhVien.lopHocDangKy).joinedload(models.SinhVienLopHoc.lopHoc_rel).options(
                    subqueryload(models.LopHoc.lichHoc), 
                    joinedload(models.LopHoc.monHoc_rel)
                ),
                # Logic CTĐT chuẩn
                joinedload(models.SinhVien.ct_dt).options(
                    joinedload(models.CT_DT.khoa_rel),
                    subqueryload(models.CT_DT.ct_ctdt)
                        .joinedload(models.CT_CTDT.nhomMH)
                            .subqueryload(models.NhomMH.ct_nmh)
                                .joinedload(models.CT_NMH.monHoc_rel)
                )
            ).filter(models.SinhVien.maSV == ma_sv).first()

            if not sinh_vien_info:
                error_data = f"Không tìm thấy hồ sơ SV ({ma_sv})."

    except Exception as e:
        print(f"LỖI DASHBOARD: {e}") 
        error_data = f"Lỗi hệ thống: {str(e)}"

    # Đọc lịch sử chat để hiển thị
    chat_history = []
    if os.path.exists(CHAT_FILE):
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                all_msgs = json.load(f)
                chat_history = [m for m in all_msgs if m.get("username") == username]
        except:
            chat_history = []

    return templates.TemplateResponse("html/dashboard.html", {
        "request": request, 
        "username": username, 
        "sinh_vien": sinh_vien_info, 
        "error_data": error_data,
        "chat_history": chat_history
    })