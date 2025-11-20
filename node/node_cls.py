import json
from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from .config import AgentState, llm_gemini
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent  # parent của node/
json_path = BASE_DIR / "describe" / "describe_pdf.json"

with open(json_path, 'r', encoding='utf-8') as f:
    policies = json.load(f)

full_desc_lines = []
for p in policies:
    for k, v in p.items():
        json_file = f"{k}.json"
        full_desc_lines.append(f"{json_file}: {v}")
FULL_DESCRIPTION = "\n\n".join(full_desc_lines)

FEW_SHOT_EXAMPLES = """
H: Một tín bao nhiêu tiền?
Đ: MucThu.json

H: Tôi bị kỷ luật vì đi trễ, có bị buộc thôi học không?
Đ: KhenThuongKyLuat.json

H: Tôi có được giảm học phí vì gia đình khó khăn không?
Đ: ChinhSachSV.json,HocBong.json

H: Tôi bị ốm không thể dự thi, có được bảo lưu kết quả không?
Đ: DanhGiaKQHT.json,QuyCheDaoTao.json

H: Tôi cần gì để đăng ký học bổng?
Đ: HocBong.json

H: Tôi đã qua môn Python chưa?
Đ: CongNhanMonHoc.json,DanhGiaKQHT.json

H: Đi thi cần mang gì?
Đ: QuyCheDaoTao.json
"""



# 1. Phân loại
cls_system_template = SystemMessagePromptTemplate.from_template(
    '''Bạn là chuyên gia phân loại chính sách sinh viên HaUI.
Dựa vào mô tả chi tiết của từng file JSON và các ví dụ mẫu, hãy xác định **chính xác các file JSON liên quan** đến câu hỏi của sinh viên.

**QUY TẮC BẮT BUỘC**:
- Đọc kỹ **toàn bộ mô tả** của từng file.
- Chọn **tất cả** các file JSON phù hợp, liệt kê cách nhau bằng dấu phẩy: `File1.json,File2.json`
- Nếu nội dung truy vấn của người dùng không liên quan đến các nội dung file đã được mô tả** thì trả về chính xác: `Không xác định`
- **Chỉ trả về đúng 1 dòng**, không giải thích, không thêm ký tự thừa.'''
)

cls_human_template = HumanMessagePromptTemplate.from_template(
    """
--- MÔ TẢ CHI TIẾT CÁC FILE JSON (ĐỌC KỸ) ---
{description}

--- VÍ DỤ PHÂN LOẠI (HỌC THEO MẪU) ---
{examples}

--- CÂU HỎI CẦN PHÂN LOẠI ---
{user_query}
    """
)
cls_prompt = ChatPromptTemplate.from_messages([cls_system_template, cls_human_template])

def node_cls(state: AgentState) -> AgentState:
    chain = cls_prompt | llm_gemini| CommaSeparatedListOutputParser()
    response = chain.invoke({
        "description": FULL_DESCRIPTION,
        "examples": FEW_SHOT_EXAMPLES,
        "user_query": state['query']
    })
    state['category'] = response
    return state

# input_state = AgentState(query='Nhà tôi nghèo, có nhận được học bổng không')
# res = node_cls(input_state)
# print(res['category'])







