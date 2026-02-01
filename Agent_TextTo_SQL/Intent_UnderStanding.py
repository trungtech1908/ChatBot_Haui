import json
from typing import Dict, Any, List

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field


# =========================
# PATH (ĐÚNG TÊN FILE CỦA BẠN)
# =========================

DB_DESCRIPTION_PATH = "/home/trung/Project_AI/Chatbot_Haui/describe/describe_DB.json"
STEP2_OUTPUT_PATH = "/home/trung/Project_AI/Chatbot_Haui/Agent_TextTo_SQL/Intent_Understanding_output.json"


# =========================
# LOAD DB DESCRIPTION
# =========================

def load_db_schema(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# OUTPUT SCHEMA (BẮT BUỘC)
# =========================

class IntentUnderstanding(BaseModel):
    intent: str

    semantic_entities: Dict[str, Any]

    db_resolution_plan: str

    tables: List[str]

    columns: List[str]

    logic: str

    semantic_answer: str


# =========================
# PROMPT
# =========================

INTENT_PROMPT = """
Bạn là AI Intent Understanding cho hệ thống quản lý sinh viên.

QUY TẮC:
- Người dùng dùng ngôn ngữ tự nhiên
- DB dùng khóa kỹ thuật (maSV, maMH…)
- KHÔNG gán chữ trực tiếp vào cột mã
- Nếu người dùng nói tên → mô tả cách tra bảng khác để lấy mã
- CHỈ dùng bảng & cột có trong schema
- KHÔNG sinh SQL
- Chỉ xét SINH VIÊN HIỆN TẠI

DATABASE SCHEMA:
{db_schema}

USER QUERY:
{user_query}

RAG CONTEXT:
{rag_context}

NHIỆM VỤ:
1. Intent
2. Semantic entities
3. Kế hoạch ánh xạ semantic → DB key
4. Bảng & cột
5. Logic xử lý
6. Câu trả lời ngữ nghĩa

{format_instructions}
"""


# =========================
# STEP 2
# =========================

def step2_intent_understanding(
    user_query: str,
    rag_context: str = ""
) -> Dict[str, Any]:

    db_schema = load_db_schema(DB_DESCRIPTION_PATH)
    parser = JsonOutputParser(pydantic_object=IntentUnderstanding)

    prompt = INTENT_PROMPT.format(
        db_schema=json.dumps(db_schema, ensure_ascii=False, indent=2),
        user_query=user_query,
        rag_context=rag_context if rag_context else "[]",
        format_instructions=parser.get_format_instructions()
    )

    llm = ChatOllama(model="qwen2.5:7b", temperature=0)
    response = llm.invoke([HumanMessage(content=prompt)])

    result = parser.parse(response.content)

    # GHI RA FILE JSON CHO BƯỚC 3
    with open(STEP2_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


# =========================
# RUN
# =========================

if __name__ == "__main__":
    step2_intent_understanding(
        user_query="Điểm môn Python của tôi là bao nhiêu",
        rag_context=""
    )
