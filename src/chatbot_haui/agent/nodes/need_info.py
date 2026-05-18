from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.agent.state import AgentState, llm_fast
from chatbot_haui.agent.nodes.parsers import parse_json_object

NEED_INFO_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn là Agent 2 — quyết định có cần tra cứu tài liệu quy chế (vector DB) không.

Trả lời JSON: {{"needs_retrieval": true/false, "needs_db": true/false, "reason": "..."}}

needs_retrieval = true khi câu hỏi về quy định, quy chế, học phí, học bổng, kỷ luật, điểm, tín chỉ, thi cử...
needs_retrieval = false khi chỉ chào hỏi, cảm ơn, hỏi chung chung không cần quy chế.

needs_db = true khi sinh viên hỏi về BẢN THÂN (tôi/em có...?, điểm của tôi, em có đủ điều kiện không)
và cần so sánh với quy chế hoặc dữ liệu cá nhân (GPA, nợ HP, đối tượng chính sách...).
needs_db = false khi chỉ hỏi quy định chung, không cần dữ liệu cá nhân."""),
    ("human", """Câu hỏi đã rewrite: {question}
Bộ nhớ Zep (nếu có): {zep_context}"""),
])


def node_need_info(state: AgentState) -> AgentState:
    chain = NEED_INFO_PROMPT | llm_fast | StrOutputParser()
    raw = chain.invoke({
        "question": state.get("new_query") or state["query"],
        "zep_context": (state.get("zep_context") or "")[:1500],
    })
    parsed = parse_json_object(raw)
    state["needs_retrieval"] = bool(parsed.get("needs_retrieval", True))
    state["needs_db"] = bool(parsed.get("needs_db", False))
    return state
