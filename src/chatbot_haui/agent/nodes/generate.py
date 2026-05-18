from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.agent.state import AgentState, llm

GENERATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn là trợ lý tư vấn quy chế sinh viên Trường Đại học Công nghiệp Hà Nội (HaUI).

Quy tắc:
- Trả lời tiếng Việt, rõ ràng, đúng câu hỏi.
- Nếu có ngữ cảnh quy chế (RAG): CHỈ dựa vào đó, không bịa điều khoản.
- Nếu có dữ liệu CSDL sinh viên: dùng để so sánh điều kiện (vd GPA vs ngưỡng học bổng).
- Nếu thiếu thông tin: nói rõ thiếu gì, không suy đoán.
- Không dùng bảng markdown; liệt kê bằng văn bản.
- Không tiết lộ mật khẩu, dữ liệu sinh viên khác.

Bộ nhớ hội thoại (Zep):
{zep_context}"""),
    ("human", """{context_block}

Câu hỏi: {user_query}"""),
])


def _build_context_block(state: AgentState) -> str:
    parts = []
    rag = state.get("retriever") or []
    if rag:
        parts.append("--- NGỮ CẢNH QUY CHẾ (Vector DB) ---\n" + "\n---\n".join(rag))
    db = state.get("db_context")
    if db:
        parts.append("--- DỮ LIỆU SINH VIÊN (CSDL) ---\n" + db)
    if not parts:
        parts.append("(Không có ngữ cảnh bổ sung — trả lời dựa kiến thức chung hoặc nói không đủ thông tin.)")
    return "\n\n".join(parts)


def node_generate(state: AgentState) -> AgentState:
    chain = GENERATE_PROMPT | llm | StrOutputParser()
    state["answer"] = chain.invoke({
        "zep_context": state.get("zep_context") or "Không có.",
        "context_block": _build_context_block(state),
        "user_query": state.get("new_query") or state["query"],
    })
    return state

