import json
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


# =========================
# OUTPUT SCHEMA
# =========================

class QueryPlan(BaseModel):
    plan_type: str = Field(description="Loại kế hoạch truy vấn")
    steps: list = Field(description="Danh sách các bước truy vấn logic")
    security_constraints: list = Field(description="Luật bảo mật bắt buộc")


# =========================
# PROMPT STEP 3
# =========================

STEP3_PROMPT = """
Bạn là AI lập kế hoạch truy vấn dữ liệu sinh viên.

DATABASE SCHEMA:
{db_schema}

INTENT JSON (từ bước 2):
{intent_json}

SINH VIÊN HIỆN TẠI:
- maSV = {current_maSV}

NHIỆM VỤ:
1. KHÔNG sinh SQL
2. Chuyển intent thành kế hoạch truy vấn từng bước
3. Nếu người dùng hỏi theo TÊN (ví dụ tên môn), phải có bước tra mã trước
4. MỌI truy vấn dữ liệu sinh viên BẮT BUỘC lọc theo maSV hiện tại
5. Trả về JSON đúng schema

KHÔNG ĐƯỢC:
- Suy đoán dữ liệu
- Bỏ điều kiện maSV
- Truy vấn sinh viên khác
"""


# =========================
# STEP 3 CORE
# =========================

def step3_query_planning(
    intent_json: Dict[str, Any],
    db_schema: Dict[str, Any],
    current_maSV: str
) -> Dict[str, Any]:

    llm = ChatOllama(
        model="qwen2.5:7b",
        reasoning=False
    )

    parser = JsonOutputParser(pydantic_object=QueryPlan)

    prompt = STEP3_PROMPT.format(
        db_schema=json.dumps(db_schema, ensure_ascii=False, indent=2),
        intent_json=json.dumps(intent_json, ensure_ascii=False, indent=2),
        current_maSV=current_maSV
    )

    message = HumanMessage(content=prompt)

    response = llm.invoke([message])

    return parser.parse(response.content)


# =========================
# DEMO CALL
# =========================
if __name__ == "__main__":
    intent_demo = {
        "intent": "Tra cứu điểm môn học của sinh viên",
        "entities": {
            "tenMonHoc": "Python"
        },
        "tables": ["monHoc", "ketQuaMonHoc"],
        "columns": ["diemGPA", "diemChu"],
        "logic": "Lấy điểm môn Python của sinh viên hiện tại",
        "semantic_answer": ""
    }

    db_schema_demo = {
        "sinhVien": ["maSV", "hoTen", "email"],
        "monHoc": ["maMH", "tenMonHoc"],
        "ketQuaMonHoc": ["maSV", "maMH", "diemGPA", "diemChu", "hocLai"]
    }

    plan = step3_query_planning(
        intent_json=intent_demo,
        db_schema=db_schema_demo,
        current_maSV="SV123"
    )

    print(json.dumps(plan, ensure_ascii=False, indent=2))
