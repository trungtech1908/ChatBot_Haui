import json
from pathlib import Path
from sqlalchemy.orm import Session
import database.models as models
from database.schemas import *

# Cấu hình nạp dữ liệu
UPLOAD_CONFIG = [
    {"name": "Khoa", "file_name": "06_khoa.json", "model_create": KhoaCreate, "model_db": models.Khoa},
    {"name": "DoanhNghiep", "file_name": "22_doanh_nghiep.json", "model_create": DoanhNghiepCreate, "model_db": models.DoanhNghiep},
    {"name": "KhoangThuKhac", "file_name": "24_khoang_thu_khac.json", "model_create": KhoangThuKhacCreate, "model_db": models.KhoangThuKhac},
    {"name": "LichThi", "file_name": "18_lich_thi.json", "model_create": LichThiCreate, "model_db": models.LichThi},
    {"name": "GiangVien", "file_name": "13_giang_vien.json", "model_create": GiangVienCreate, "model_db": models.GiangVien},
    {"name": "MonHoc", "file_name": "08_mon_hoc.json", "model_create": MonHocCreate, "model_db": models.MonHoc},
    {"name": "NhomMH", "file_name": "09_nhom_mh.json", "model_create": NhomMHCreate, "model_db": models.NhomMH},
    {"name": "CT_DT", "file_name": "07_ctdt.json", "model_create": CT_DTCreate, "model_db": models.CT_DT},
    {"name": "CT_CTDT", "file_name": "10_ct_ctdt.json", "model_create": CT_CTDTCreate, "model_db": models.CT_CTDT},
    {"name": "CT_NMH", "file_name": "11_ct_nmh.json", "model_create": CT_NMHCreate, "model_db": models.CT_NMH},
    {"name": "TQMH", "file_name": "12_tqmh.json", "model_create": TQMHCreate, "model_db": models.TQMH},
    {"name": "PhuTrach", "file_name": "21_phu_trach.json", "model_create": PhuTrachCreate, "model_db": models.PhuTrach}, 
    {"name": "SinhVien", "file_name": "01_sinh_vien.json", "model_create": SinhVienCreate, "model_db": models.SinhVien},
    {"name": "TaiChinh", "file_name": "02_tai_chinh.json", "model_create": TaiChinhCreate, "model_db": models.TaiChinh},
    {"name": "DoiTuong", "file_name": "03_doi_tuong.json", "model_create": DoiTuongCreate, "model_db": models.DoiTuong},
    {"name": "DieuKienTotNghiep", "file_name": "04_dk_tn.json", "model_create": DieuKienTotNghiepCreate, "model_db": models.DieuKienTotNghiep},
    {"name": "TaiKhoan", "file_name": "05_tai_khoan.json", "model_create": TaiKhoanCreate, "model_db": models.TaiKhoan},
    {"name": "ThucTap", "file_name": "23_thuc_tap.json", "model_create": ThucTapCreate, "model_db": models.ThucTap}, 
    {"name": "LopHoc", "file_name": "14_lop_hoc.json", "model_create": LopHocCreate, "model_db": models.LopHoc}, 
    {"name": "LichHoc", "file_name": "17_lich_hoc.json", "model_create": LichHocCreate, "model_db": models.LichHoc}, 
    {"name": "SinhVienLopHoc", "file_name": "19_sv_lh.json", "model_create": SinhVienLopHocCreate, "model_db": models.SinhVienLopHoc}, 
    {"name": "KetQuaHocKy", "file_name": "16_kqhk.json", "model_create": KetQuaHocKyCreate, "model_db": models.KetQuaHocKy},
    {"name": "KetQuaMonHoc", "file_name": "15_kqmh.json", "model_create": KetQuaMonHocCreate, "model_db": models.KetQuaMonHoc}, 
    {"name": "LichThiSV", "file_name": "20_lich_thi_sv.json", "model_create": LichThiSVCreate, "model_db": models.LichThiSV}, 
    {"name": "GiaoDich", "file_name": "25_giao_dich.json", "model_create": GiaoDichCreate, "model_db": models.GiaoDich}, 
    {"name": "LSGD", "file_name": "26_lsgd.json", "model_create": LSGDCreate, "model_db": models.LSGD},
]

JSON_DIR = "json"

def bulk_create_records(db: Session, records: list, model_db: type):
    if not records: return 0
    db_items = [model_db(**record.model_dump(exclude_unset=True, by_alias=False)) for record in records]
    db.bulk_save_objects(db_items)
    db.commit()
    return len(db_items)

def seed_database(db: Session):
    """Hàm nạp dữ liệu từ JSON vào DB"""
    for config in UPLOAD_CONFIG:
        file_name = config["file_name"]
        ModelCreate = config["model_create"]
        ModelDB = config["model_db"]
        file_path = Path(JSON_DIR) / file_name
        
        if not file_path.exists(): continue
            
        try:
            if db.query(ModelDB).first() is None:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                records = [ModelCreate(**item) for item in raw_data]
                count = bulk_create_records(db, records, ModelDB)
                print(f"✅ Đã nạp {count} bản ghi cho bảng '{ModelDB.__tablename__}'.")
        except Exception as e:
            db.rollback()
            print(f"❌ Lỗi nạp '{file_name}': {e}")