from langchain_core.prompts import ChatPromptTemplate
from .config import AgentState, llm

prompt = ChatPromptTemplate.from_messages([
    ("system", "Bạn là trợ lý AI. Trả lời bằng tiếng Việt, chi tiết, đầy đủ, không tóm tắt."),
    ("human", "Ngữ cảnh:\n{retriever}\n\nCâu hỏi: {user_query}")
])

async def node_answer(state: AgentState):
    chain = prompt | llm
    async for chunk in chain.astream({
        "retriever": "\n".join(state.get("retriever", [])) or "Không có thông tin.",
        "user_query": state["new_query"]
    }):
        if chunk.content:
            # CHỈ YIELD partial_answer → web nhận được ngay
            yield {"partial_answer": chunk.content}