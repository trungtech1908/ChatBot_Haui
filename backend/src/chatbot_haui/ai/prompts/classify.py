import json
from pathlib import Path

UNKNOWN = "Không xác định"

# Mô tả từng tài liệu; key trùng tên PDF (không đuôi) và trùng source trong Qdrant
with open(Path(__file__).with_name("document_descriptions.json"), encoding="utf-8") as f:
    DOCUMENT_DESCRIPTIONS = "\n\n".join(f"{k}: {v}" for doc in json.load(f) for k, v in doc.items())

FEW_SHOT_EXAMPLES = """
H: Một tín bao nhiêu tiền?
Đ: MucThuHP

H: Tôi bị kỷ luật vì đi trễ, có bị buộc thôi học không?
Đ: KhenThuongKyLuat

H: Tôi có được giảm học phí vì gia đình khó khăn không?
Đ: ChinhSachSV,HocBong

H: Tôi bị ốm không thể dự thi, có được bảo lưu kết quả không?
Đ: DanhGiaKQHT,QuyCheDaoTao

H: Tôi cần gì để đăng ký học bổng?
Đ: HocBong

H: Tôi đã qua môn Python chưa?
Đ: CongNhanMonHocTamThoi,DanhGiaKQHT

H: Đi thi cần mang gì?
Đ: QuyCheDaoTao
"""

SYSTEM_PROMPT = """Bạn là chuyên gia phân loại chính sách sinh viên HaUI.
Dựa vào mô tả chi tiết của từng tài liệu và các ví dụ mẫu, hãy xác định **chính xác các tài liệu liên quan** đến câu hỏi của sinh viên.

**QUY TẮC BẮT BUỘC**:
- Đọc kỹ **toàn bộ mô tả** của từng tài liệu.
- Chọn **tất cả** các tài liệu phù hợp, ghi đúng tên tài liệu như trong mô tả, cách nhau bằng dấu phẩy: `TaiLieu1,TaiLieu2`
- Nếu nội dung truy vấn của người dùng không liên quan đến các tài liệu đã được mô tả thì trả về chính xác: `Không xác định`
- **Chỉ trả về đúng 1 dòng**, không giải thích, không thêm ký tự thừa."""

HUMAN_PROMPT = """
--- MÔ TẢ CHI TIẾT CÁC TÀI LIỆU (ĐỌC KỸ) ---
{description}

--- VÍ DỤ PHÂN LOẠI (HỌC THEO MẪU) ---
{examples}

--- CÂU HỎI CẦN PHÂN LOẠI ---
{user_query}
"""
