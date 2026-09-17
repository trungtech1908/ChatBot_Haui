"""Nạp dữ liệu mẫu từ assets/seed/*.json vào MySQL (bỏ qua bảng đã có dữ liệu)."""
import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from chatbot_haui.core.config import settings
from chatbot_haui.core.security import hash_password
from chatbot_haui.db import models
from chatbot_haui.schema.seed import *  # noqa: F403

logger = logging.getLogger(__name__)

# Theo thứ tự khóa ngoại: bảng cha trước, bảng con sau
SEED_TABLES = [
    ("06_khoa.json", KhoaCreate, models.Khoa),
    ("22_doanh_nghiep.json", DoanhNghiepCreate, models.DoanhNghiep),
    ("24_khoang_thu_khac.json", KhoangThuKhacCreate, models.KhoangThuKhac),
    ("18_lich_thi.json", LichThiCreate, models.LichThi),
    ("13_giang_vien.json", GiangVienCreate, models.GiangVien),
    ("08_mon_hoc.json", MonHocCreate, models.MonHoc),
    ("09_nhom_mh.json", NhomMHCreate, models.NhomMH),
    ("07_ctdt.json", CT_DTCreate, models.CT_DT),
    ("10_ct_ctdt.json", CT_CTDTCreate, models.CT_CTDT),
    ("11_ct_nmh.json", CT_NMHCreate, models.CT_NMH),
    ("12_tqmh.json", TQMHCreate, models.TQMH),
    ("21_phu_trach.json", PhuTrachCreate, models.PhuTrach),
    ("01_sinh_vien.json", SinhVienCreate, models.SinhVien),
    ("02_tai_chinh.json", TaiChinhCreate, models.TaiChinh),
    ("03_doi_tuong.json", DoiTuongCreate, models.DoiTuong),
    ("04_dk_tn.json", DieuKienTotNghiepCreate, models.DieuKienTotNghiep),
    ("05_tai_khoan.json", TaiKhoanCreate, models.TaiKhoan),
    ("23_thuc_tap.json", ThucTapCreate, models.ThucTap),
    ("14_lop_hoc.json", LopHocCreate, models.LopHoc),
    ("17_lich_hoc.json", LichHocCreate, models.LichHoc),
    ("19_sv_lh.json", SinhVienLopHocCreate, models.SinhVienLopHoc),
    ("16_kqhk.json", KetQuaHocKyCreate, models.KetQuaHocKy),
    ("15_kqmh.json", KetQuaMonHocCreate, models.KetQuaMonHoc),
    ("20_lich_thi_sv.json", LichThiSVCreate, models.LichThiSV),
    ("25_giao_dich.json", GiaoDichCreate, models.GiaoDich),
    ("26_lsgd.json", LSGDCreate, models.LSGD),
]


def seed_database(db: Session):
    for file_name, schema, model in SEED_TABLES:
        path = settings.seed_dir / file_name
        if not path.exists() or db.scalar(select(model).limit(1)) is not None:
            continue
        rows = [schema(**item).model_dump(exclude_unset=True) for item in json.loads(path.read_text(encoding="utf-8"))]
        if model is models.TaiKhoan:
            for row in rows:
                row["matKhau"] = hash_password(row["matKhau"])
        db.add_all(model(**row) for row in rows)
        db.commit()
        logger.info("Đã nạp %d bản ghi vào %s", len(rows), model.__tablename__)
