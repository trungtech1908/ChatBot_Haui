from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.agent.state import AgentState, llm_fast
from chatbot_haui.agent.nodes.parsers import parse_json_object

QUALITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn là Agent 4 — kiểm tra chất lượng câu trả lời.

JSON: {{
  "quality_ok": true/false,
  "feedback": "lý do ngắn nếu chưa ổn"
}}

quality_ok=false khi:
- Không trả lời đúng câu hỏi
- Bịa thông tin không có trong ngữ cảnh
- Mâu thuẫn dữ liệu CSDL/quy chế
- Quá chung chung khi đã có đủ context"""),
    ("human", """Câu hỏi gốc: {query}
Câu hỏi rewrite: {new_query}
Có RAG: {has_rag}
Có DB: {has_db}

Ngữ cảnh quy chế (rút gọn):
{rag_snippet}

Dữ liệu SV:
{db_snippet}

Câu trả lời:
{answer}"""),
])


def node_quality_check(state: AgentState) -> AgentState:
    chain = QUALITY_PROMPT | llm_fast | StrOutputParser()
    raw = chain.invoke({
        "query": state["query"],
        "new_query": state.get("new_query") or state["query"],
        "has_rag": bool(state.get("retriever")),
        "has_db": bool(state.get("db_context")),
        "rag_snippet": "\n".join((state.get("retriever") or [])[:2])[:1500],
        "db_snippet": (state.get("db_context") or "")[:800],
        "answer": state.get("answer") or "",
    })
    parsed = parse_json_object(raw)
    state["quality_ok"] = bool(parsed.get("quality_ok", False))
    state["quality_feedback"] = str(parsed.get("feedback", ""))
    return state
