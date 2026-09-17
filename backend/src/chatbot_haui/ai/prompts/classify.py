import json
from pathlib import Path

UNKNOWN = "Không xác định"

# Mô tả từng tài liệu; key trùng tên PDF, source trong Qdrant là "<key>.json"
with open(Path(__file__).with_name("document_descriptions.json"), encoding="utf-8") as f:
    DOCUMENT_DESCRIPTIONS = "\n\n".join(f"{k}.json: {v}" for doc in json.load(f) for k, v in doc.items())

FEW_SHOT_EXAMPLES = """
H: Một tín bao nhiêu tiền?
Đ: MucThuHP.json

H: Tôi bị kỷ luật vì đi trễ, có bị buộc thôi học không?
Đ: KhenThuongKyLuat.json

H: Tôi có được giảm học phí vì gia đình khó khăn không?
Đ: ChinhSachSV.json,HocBong.json

H: Tôi bị ốm không thể dự thi, có được bảo lưu kết quả không?
Đ: DanhGiaKQHT.json,QuyCheDaoTao.json

H: Tôi cần gì để đăng ký học bổng?
Đ: HocBong.json

H: Tôi đã qua môn Python chưa?
Đ: CongNhanMonHocTamThoi.json,DanhGiaKQHT.json

H: Đi thi cần mang gì?
Đ: QuyCheDaoTao.json
"""

SYSTEM_PROMPT = """Bạn là chuyên gia phân loại chính sách sinh viên HaUI.
Dựa vào mô tả chi tiết của từng file JSON và các ví dụ mẫu, hãy xác định **chính xác các file JSON liên quan** đến câu hỏi của sinh viên.

**QUY TẮC BẮT BUỘC**:
- Đọc kỹ **toàn bộ mô tả** của từng file.
- Chọn **tất cả** các file JSON phù hợp, liệt kê cách nhau bằng dấu phẩy: `File1.json,File2.json`
- Nếu nội dung truy vấn của người dùng không liên quan đến các nội dung file đã được mô tả thì trả về chính xác: `Không xác định`
- **Chỉ trả về đúng 1 dòng**, không giải thích, không thêm ký tự thừa."""

HUMAN_PROMPT = """
--- MÔ TẢ CHI TIẾT CÁC FILE JSON (ĐỌC KỸ) ---
{description}

--- VÍ DỤ PHÂN LOẠI (HỌC THEO MẪU) ---
{examples}

--- CÂU HỎI CẦN PHÂN LOẠI ---
{user_query}
"""
