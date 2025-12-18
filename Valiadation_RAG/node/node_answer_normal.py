from .config import AgentState, llm

def node_answer_normal(state: AgentState) -> dict:
    answer = llm.invoke(state["new_query"]).content
    return {"answer": answer}   # không print gì hết