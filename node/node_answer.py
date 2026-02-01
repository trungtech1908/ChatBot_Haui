from langchain_core.prompts import ChatPromptTemplate
from .config import AgentState, llm

prompt = ChatPromptTemplate.from_messages([
    ("system", "Bạn là trợ lý AI. Bạn sẽ dựa vào ngữ cảnh được cho và câu hỏi người dùng, Trả lời bằng tiếng Việt, chi tiết, đầy đủ, không tóm tắt. "
               "Nếu ngữ cảnh có dữ liệu bảng hay markdown, hãy đơn trả lời dưới dạng liệt kê hoặc mô tả, không sử dụng bảng hay markdown. Trả lời một cách đầy đủ, chi tiết nếu nội dung trong bảng hay mark down có liên quan tới câu hỏi"),
    ("human", "Ngữ cảnh:\n{retriever}\n\nCâu hỏi: {user_query}")
])


def node_answer(state: AgentState) -> AgentState:
    chain = prompt | llm
    state['answer'] = chain.invoke({
        "retriever": "\n".join(state.get("retriever", [])) or "Không có thông tin.",
        "user_query": state["new_query"]
    }).content
    return state
