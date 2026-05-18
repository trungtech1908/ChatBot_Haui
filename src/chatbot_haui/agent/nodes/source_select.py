"""Agent 3 — chọn nguồn tài liệu trong vector DB (theo file quy chế)."""

import json

from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.agent.state import AgentState, llm_fast

from chatbot_haui.paths import KNOWLEDGE_DIR

json_path = KNOWLEDGE_DIR / "describe_pdf.json"

with open(json_path, encoding="utf-8") as f:
    policies = json.load(f)

FULL_DESCRIPTION = "\n\n".join(
    f"{k}.json: {v}" for p in policies for k, v in p.items()
)

FEW_SHOT_EXAMPLES = """
H: Một tín bao nhiêu tiền?
Đ: MucThu.json

H: Tôi có được giảm học phí vì gia đình khó khăn không?
Đ: ChinhSachSV.json,HocBong.json

H: Tôi có nhận được học bổng không?
Đ: HocBong.json,HocBongNTB.json,DRL.json

H: Điểm rèn luyện tính thế nào để được học bổng?
Đ: DRL.json,HocBong.json
"""

CLS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn là Agent 3 — chọn file quy chế trong vector DB.
Chọn TẤT CẢ file JSON liên quan, cách nhau bằng dấu phẩy: File1.json,File2.json
Nếu không liên quan quy chế HaUI → trả về: Không xác định
Chỉ 1 dòng, không giải thích."""),
    ("human", """Mô tả file:
{description}

Ví dụ:
{examples}

Câu hỏi: {user_query}"""),
])


def node_source_select(state: AgentState) -> AgentState:
    chain = CLS_PROMPT | llm_fast | CommaSeparatedListOutputParser()
    response = chain.invoke({
        "description": FULL_DESCRIPTION,
        "examples": FEW_SHOT_EXAMPLES,
        "user_query": state.get("new_query") or state["query"],
    })
    state["category"] = response
    return state
