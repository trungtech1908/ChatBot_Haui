from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.agent.state import AgentState, llm_fast

REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn là Agent 1 — tối ưu câu hỏi cho hệ thống RAG quy chế sinh viên HaUI.
Nhiệm vụ: sửa chính tả, làm rõ ý, đơn giản hóa, chuẩn hóa từ lóng → thuật ngữ chính thức.
Giữ nguyên ý gốc. Không thêm thông tin ngoài câu hỏi.
Chỉ trả về ĐÚNG 1 câu hỏi tối ưu (tiếng Việt), không giải thích."""),
    ("human", """{feedback_block}Câu hỏi gốc: {user_query}"""),
])


def node_query_transform(state: AgentState) -> AgentState:
    feedback = state.get("quality_feedback") or ""
    feedback_block = ""
    if feedback:
        feedback_block = f"Phản hồi kiểm tra chất lượng (cần cải thiện): {feedback}\n\n"

    chain = REWRITE_PROMPT | llm_fast | StrOutputParser()
    state["new_query"] = chain.invoke({
        "user_query": state["query"],
        "feedback_block": feedback_block,
    }).strip()
    return state
