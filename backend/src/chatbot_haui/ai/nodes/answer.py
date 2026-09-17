from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.ai.llm import get_llm
from chatbot_haui.ai.prompts import answer as prompts
from chatbot_haui.ai.state import AgentState

chain = ChatPromptTemplate.from_messages([("system", prompts.SYSTEM_PROMPT), ("human", prompts.HUMAN_PROMPT)]) | get_llm()


# Token được stream ra ngoài qua astream_events, node chỉ cần trả câu trả lời cuối
async def answer(state: AgentState) -> dict:
    response = await chain.ainvoke({
        "retriever": "\n".join(state.get("retriever") or []) or "Không có thông tin.",
        "user_query": state["new_query"],
    })
    return {"answer": response.content}


async def answer_general(state: AgentState) -> dict:
    response = await get_llm().ainvoke(state["new_query"])
    return {"answer": response.content}
