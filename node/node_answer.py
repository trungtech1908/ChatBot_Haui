from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

from .config import AgentState, llm
answer_system_template = SystemMessagePromptTemplate.from_template(
    "Bạn là trợ lý AI. Luôn trả lời câu hỏi của người dùng bằng tiếng Việt.\n"
    "Câu trả lời của bạn phải chi tiết và **đầy đủ**, nội dung liên quan trong ngữ cảnh.\n"
    "KHÔNG được tóm tắt hoặc lược bỏ chi tiết.\n"
    "Nếu không có ngữ cảnh, hãy trả lời 'tôi không biết'."
)

answer_human_template = HumanMessagePromptTemplate.from_template(
    "Ngữ cảnh:\n{retriever}\n\nCâu hỏi của người dùng: {user_query}"
)

answer_prompt = ChatPromptTemplate.from_messages([answer_system_template, answer_human_template])

async def node_answer(state: AgentState) -> AgentState:
    chain = answer_prompt | llm
    full_response = ""
    print("\nTrả lời: ", end="", flush=True)

    async for chunk in chain.astream({
        "retriever": '\n'.join(state['retriever']) or "Không có thông tin.",
        "user_query": state['new_query']
    }):
        content = chunk.content
        print(content, end="", flush=True)
        full_response += content

    state['answer'] = full_response
    return state