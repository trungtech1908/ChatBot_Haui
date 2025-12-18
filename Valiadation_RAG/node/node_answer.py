from langchain_core.prompts import ChatPromptTemplate
from .config import AgentState, llm

prompt = ChatPromptTemplate.from_messages([
    ("system", "Bạn là trợ lý AI. Trả lời bằng tiếng Việt, chi tiết, đầy đủ, không tóm tắt."),
    ("human", "Ngữ cảnh:\n{retriever}\n\nCâu hỏi: {user_query}")
])


def node_answer(state: AgentState) -> AgentState:
    chain = prompt | llm
    state["answer"] = chain.invoke({
        "retriever": "\n".join(state.get("retriever", [])) or "Không có thông tin.",
        "user_query": state["new_query"]
    }).content
    return state
