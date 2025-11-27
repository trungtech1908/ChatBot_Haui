import json
from pathlib import Path
from typing import List
import os
# FastAPI & Pydantic
from fastapi import FastAPI, Depends, status, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles # <--- QUAN TRỌNG: Để load CSS/JS
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, ValidationError
from datetime import datetime
# Database & SQLAlchemy
from sqlalchemy.orm import Session, joinedload, subqueryload
from sqlalchemy.exc import IntegrityError, OperationalError

# Modules của bạn
import database.models as models
from database.database import SessionLocal, engine, Base, create_database_if_not_exists
from database.schemas import * 
# --- 1. CẤU HÌNH APP VÀ STATIC FILES ---
app = FastAPI(
    title="Student Management System",
    description="Hệ thống Quản lý Sinh viên với cấu trúc Template phân tách.",
    version="2.0.0"
)

# Cấu hình để truy cập file tĩnh (CSS, JS) qua đường dẫn /static
# Ví dụ: /static/css/style.css sẽ tìm trong templates/css/style.css
app.mount("/static", StaticFiles(directory="templates"), name="static")

# Cấu hình Jinja2 tìm file HTML trong thư mục templates
templates = Jinja2Templates(directory="templates")

# Cấu hình file lưu chat
CHAT_FILE = "json/chat_data.json"

# Model nhận dữ liệu từ giao diện
class ChatMessage(BaseModel):
    username: str
    message: str

# --- 2. CẤU HÌNH DỮ LIỆU JSON (Để tự động nạp khi khởi động) ---
# Giữ nguyên cấu hình này từ code cũ của bạn
UPLOAD_CONFIG = [
    # --- NHÓM 1: DỮ LIỆU NỀN TẢNG ---
    {"name": "Khoa", "file_name": "06_khoa.json", "model_create": KhoaCreate, "model_db": models.Khoa},
    {"name": "DoanhNghiep", "file_name": "22_doanh_nghiep.json", "model_create": DoanhNghiepCreate, "model_db": models.DoanhNghiep},
    {"name": "KhoangThuKhac", "file_name": "24_khoang_thu_khac.json", "model_create": KhoangThuKhacCreate, "model_db": models.KhoangThuKhac},
    {"name": "LichThi", "file_name": "18_lich_thi.json", "model_create": LichThiCreate, "model_db": models.LichThi},
    
    # --- NHÓM 2: ĐỊNH NGHĨA HỌC VỤ & GIẢNG VIÊN ---
    {"name": "GiangVien", "file_name": "13_giang_vien.json", "model_create": GiangVienCreate, "model_db": models.GiangVien},
    {"name": "MonHoc", "file_name": "08_mon_hoc.json", "model_create": MonHocCreate, "model_db": models.MonHoc},
    
    
    # --- NHÓM 3: CHI TIẾT ĐÀO TẠO (Cập nhật theo model mới) ---
    # Thay NhomTC bằng NhomMH
    {"name": "NhomMH", "file_name": "09_nhom_mh.json", "model_create": NhomMHCreate, "model_db": models.NhomMH},
    {"name": "CT_DT", "file_name": "07_ctdt.json", "model_create": CT_DTCreate, "model_db": models.CT_DT},
    {"name": "CT_CTDT", "file_name": "10_ct_ctdt.json", "model_create": CT_CTDTCreate, "model_db": models.CT_CTDT},
    {"name": "CT_NMH", "file_name": "11_ct_nmh.json", "model_create": CT_NMHCreate, "model_db": models.CT_NMH},
    
    {"name": "TQMH", "file_name": "12_tqmh.json", "model_create": TQMHCreate, "model_db": models.TQMH},
    {"name": "PhuTrach", "file_name": "21_phu_trach.json", "model_create": PhuTrachCreate, "model_db": models.PhuTrach}, 

    # --- NHÓM 4: SINH VIÊN ---
    {"name": "SinhVien", "file_name": "01_sinh_vien.json", "model_create": SinhVienCreate, "model_db": models.SinhVien},
    
    # --- NHÓM 5: DỮ LIỆU PHỤ THUỘC SINH VIÊN ---
    {"name": "TaiChinh", "file_name": "02_tai_chinh.json", "model_create": TaiChinhCreate, "model_db": models.TaiChinh},
    {"name": "DoiTuong", "file_name": "03_doi_tuong.json", "model_create": DoiTuongCreate, "model_db": models.DoiTuong},
    {"name": "DieuKienTotNghiep", "file_name": "04_dk_tn.json", "model_create": DieuKienTotNghiepCreate, "model_db": models.DieuKienTotNghiep},
    {"name": "TaiKhoan", "file_name": "05_tai_khoan.json", "model_create": TaiKhoanCreate, "model_db": models.TaiKhoan},
    {"name": "ThucTap", "file_name": "23_thuc_tap.json", "model_create": ThucTapCreate, "model_db": models.ThucTap}, 

    # --- NHÓM 6: LỚP HỌC & ĐĂNG KÝ ---
    {"name": "LopHoc", "file_name": "14_lop_hoc.json", "model_create": LopHocCreate, "model_db": models.LopHoc}, 
    {"name": "LichHoc", "file_name": "17_lich_hoc.json", "model_create": LichHocCreate, "model_db": models.LichHoc}, 
    {"name": "SinhVienLopHoc", "file_name": "19_sv_lh.json", "model_create": SinhVienLopHocCreate, "model_db": models.SinhVienLopHoc}, 

    # --- NHÓM 7: KẾT QUẢ & GIAO DỊCH ---
    {"name": "KetQuaHocKy", "file_name": "16_kqhk.json", "model_create": KetQuaHocKyCreate, "model_db": models.KetQuaHocKy},
    {"name": "KetQuaMonHoc", "file_name": "15_kqmh.json", "model_create": KetQuaMonHocCreate, "model_db": models.KetQuaMonHoc}, 
    {"name": "LichThiSV", "file_name": "20_lich_thi_sv.json", "model_create": LichThiSVCreate, "model_db": models.LichThiSV}, 
    {"name": "GiaoDich", "file_name": "25_giao_dich.json", "model_create": GiaoDichCreate, "model_db": models.GiaoDich}, 
    {"name": "LSGD", "file_name": "26_lsgd.json", "model_create": LSGDCreate, "model_db": models.LSGD},
]

JSON_DIR = "json"

# --- 3. CÁC HÀM HELPER (DATABASE) ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def bulk_create_records(db: Session, records: List[BaseModel], model_db: type):
    if not records:
        return 0
    db_items = []
    for record in records:
        data = record.model_dump(exclude_unset=True, by_alias=False) 
        db_item = model_db(**data) 
        db_items.append(db_item)
    db.bulk_save_objects(db_items) 
    db.commit()
    return len(db_items)

# --- 4. SỰ KIỆN STARTUP (Tự động tạo bảng & nạp dữ liệu) ---
@app.on_event("startup")
def startup_event_db_init():
    print("\n[STARTUP] 🚀 Đang khởi tạo Database...")
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"❌ LỖI KẾT NỐI DB: {e}")
        return

    try:
        db = next(get_db())
    except Exception as e:
        print(f"❌ KHÔNG LẤY ĐƯỢC SESSION: {e}")
        return

    for config in UPLOAD_CONFIG:
        file_name = config["file_name"]
        ModelCreate = config["model_create"]
        ModelDB = config["model_db"]
        file_path = Path(JSON_DIR) / file_name
        
        if not file_path.exists():
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            if db.query(ModelDB).count() > 0:
                 continue

            records = [ModelCreate(**item) for item in raw_data]
            count = bulk_create_records(db, records, ModelDB)
            print(f"✅ Đã nạp {count} bản ghi cho bảng '{ModelDB.__tablename__}'.")

        except Exception as e:
            db.rollback()
            print(f"❌ Lỗi nạp '{file_name}': {e}")
            
    db.close()
    print("[STARTUP] ✅ Hệ thống sẵn sàng!\n")


# --- 5. ROUTES (VIEWS) ---

# Trang Login (GET /)
@app.get("/", response_class=HTMLResponse, name="login_page")
def get_login_page(request: Request):
    # CHÚ Ý: Đường dẫn file giờ là html/login.html
    # Bạn nhớ di chuyển file login.html vào thư mục templates/html/ nhé
    return templates.TemplateResponse("html/login.html", {"request": request})

# Xử lý Login (POST /login)
@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request, 
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.TaiKhoan).filter(
        models.TaiKhoan.tenTaiKhoan == username,
        models.TaiKhoan.matKhau == password
    ).first()
    
    if user:
        # Đăng nhập thành công -> Chuyển hướng sang Dashboard
        target_url = f"/welcome?username={user.tenTaiKhoan}"
        return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    else:
        # Đăng nhập thất bại -> Render lại trang login với thông báo lỗi
        return templates.TemplateResponse(
            "html/login.html", 
            {"request": request, "error": "Tên đăng nhập hoặc mật khẩu không đúng."},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

# Dashboard Chính (GET /welcome)
@app.get("/welcome", response_class=HTMLResponse, name="welcome_dashboard")
def welcome_dashboard(request: Request, username: str, db: Session = Depends(get_db)): 
    sinh_vien_info = None
    error_data = None
    
    try:
        # Bước 1: Lấy maSV từ username
        tai_khoan = db.query(models.TaiKhoan.maSV).filter(
            models.TaiKhoan.tenTaiKhoan == username
        ).first()

        if not tai_khoan:
            error_data = "Không tìm thấy tài khoản."
        else:
            ma_sv = tai_khoan.maSV
            
            # Bước 2: Eager Loading (ĐÃ SỬA LỖI TRUY VẤN)
            sinh_vien_info = db.query(models.SinhVien).options(
                joinedload(models.SinhVien.taiChinh),
                joinedload(models.SinhVien.doiTuong), # Bảng ĐỐI TƯỢNG
                joinedload(models.SinhVien.dieuKienTotNghiep),
                joinedload(models.SinhVien.taiKhoan), 
                subqueryload(models.SinhVien.ketQuaMonHoc).options(
                    joinedload(models.KetQuaMonHoc.monHoc_rel),
                    joinedload(models.KetQuaMonHoc.ketQuaHocKy_rel) 
                ),
                
                subqueryload(models.SinhVien.giaoDich).joinedload(models.GiaoDich.lichSuGiaoDich),
                subqueryload(models.SinhVien.lichThiSV).joinedload(models.LichThiSV.lichThi_rel),
                subqueryload(models.SinhVien.thucTapRecords).options(joinedload(models.ThucTap.doanhNghiep_rel), joinedload(models.ThucTap.giangVien_rel)),
                subqueryload(models.SinhVien.lopHocDangKy).joinedload(models.SinhVienLopHoc.lopHoc_rel).options(subqueryload(models.LopHoc.lichHoc), joinedload(models.LopHoc.monHoc_rel)),
                
                # SỬA ĐỔI: Load CTĐT cùng với KHOA và Chi tiết môn học
                joinedload(models.SinhVien.ct_dt).options(
                    joinedload(models.CT_DT.khoa_rel), # <--- LẤY THÔNG TIN KHOA Ở ĐÂY
                    subqueryload(models.CT_DT.ct_ctdt)
                        .joinedload(models.CT_CTDT.nhomMH)
                            .subqueryload(models.NhomMH.ct_nmh)
                                .joinedload(models.CT_NMH.monHoc_rel)
                )

            ).filter(models.SinhVien.maSV == ma_sv).first()

            if not sinh_vien_info:
                error_data = f"Không tìm thấy hồ sơ sinh viên (Mã: {ma_sv})."
                
    except Exception as e:
        print(f"LỖI TRUY VẤN: {e}") # Xem lỗi chi tiết trong Terminal
        error_data = f"Lỗi hệ thống: {str(e)}"

    chat_history = []
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            try:
                all_msgs = json.load(f)
                # Lọc tin nhắn của user hiện tại (hoặc lấy hết nếu muốn)
                chat_history = [m for m in all_msgs if m.get("username") == username]
            except:
                chat_history = []

    # --- SỬA DÒNG RETURN: Truyền thêm chat_history vào template ---
    return templates.TemplateResponse("html/dashboard.html", {
        "request": request, 
        "username": username, 
        "sinh_vien": sinh_vien_info, 
        "error_data": error_data,
        "chat_history": chat_history  # <--- Quan trọng
    })

@app.post("/api/send_message")
async def send_message(chat_data: ChatMessage):
    # 1. Đọc dữ liệu cũ
    messages = []
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            try:
                messages = json.load(f)
            except:
                messages = []

    # 2. Thêm tin mới
    new_msg = {
        "username": chat_data.username,
        "message": chat_data.message,
        "timestamp": datetime.now().strftime("%H:%M %d/%m/%Y"),
        "sender": "user"
    }
    messages.append(new_msg)

    # 3. Lưu file
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    return {"status": "success", "data": new_msg}

# Xóa lịch sử chat của user (POST /api/reset_chat)
class DeleteChatRequest(BaseModel):
    username: str

@app.post("/api/reset_chat")
async def reset_chat(data: DeleteChatRequest):
    if not os.path.exists(CHAT_FILE):
        return {"status": "success", "message": "File không tồn tại"}

    # 1. Đọc toàn bộ tin nhắn
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        try:
            all_messages = json.load(f)
        except:
            all_messages = []

    # 2. Giữ lại tin nhắn KHÔNG PHẢI của user này
    # (Lọc bỏ các tin nhắn có username trùng với user đang yêu cầu xóa)
    remaining_messages = [msg for msg in all_messages if msg.get("username") != data.username]

    # 3. Ghi lại vào file
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(remaining_messages, f, ensure_ascii=False, indent=2)

    return {"status": "success", "message": "Đã xóa lịch sử chat"}

# Đăng xuất (GET /logout)
@app.get("/logout")
def logout():
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)