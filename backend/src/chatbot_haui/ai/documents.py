"""Danh mục văn bản quy chế đang có trên Qdrant (payload `source` = tên PDF không đuôi).

Danh sách văn bản = các key trong prompts/document_descriptions.json (thêm PDF mới thì thêm mô tả ở đó).
`title` dùng để trích dẫn trong câu trả lời (thiếu thì dùng mã văn bản); `description` để Planner chọn văn bản cần lọc.
Số quyết định lấy theo haui_db/ARCHITECTURE.md mục 5; văn bản nào bản gốc mất số QĐ thì không ghi.
"""
import json
from pathlib import Path

_DESCRIPTIONS = {
    k: v
    for doc in json.loads((Path(__file__).parent / "prompts" / "document_descriptions.json").read_text(encoding="utf-8"))
    for k, v in doc.items()
}

TITLES = {
    "HocBong": "Quy định xét học bổng (QĐ 725/QĐ-ĐHCN)",
    "HocBongNTB": "Quy chế học bổng khuyến học Nguyễn Thanh Bình (QĐ 279/QĐ-ĐHCN)",
    "MucThuHP": "Mức thu học phí năm học 2025-2026 (QĐ 778/QĐ-ĐHCN)",
    "TinhHocPhi": "Quy định tính học phí lớp học phần",
    "KhoanThu": "Quy định các khoản thu năm học 2025-2026 (QĐ 1659/QĐ-ĐHCN)",
    "ThuPhiKhongXemLai": "Thông báo thu phí không đến xem lại bài thi",
    "ChinhSachSV": "Quy định thực hiện chính sách cho sinh viên",
    "DRL": "Quy định đánh giá kết quả rèn luyện",
    "DanhGiaKQHT": "Quy định đánh giá kết quả học tập",
    "QuyCheDaoTao": "Quy chế đào tạo",
    "KhenThuongKyLuat": "Quy định khen thưởng, kỷ luật sinh viên",
    "CongNhanMonHocTamThoi": "Quy định công nhận kết quả học tập và chuyển đổi tín chỉ",
    "QuyCheCTSV": "Quy chế công tác sinh viên",
}
SOURCES = list(_DESCRIPTIONS)


def title(source: str) -> str:
    return TITLES.get(source, source)


def catalog() -> str:
    """Danh sách văn bản cho prompt Planner."""
    return "\n".join(f"- {s}: {title(s)}. {_DESCRIPTIONS[s]}" for s in SOURCES)
