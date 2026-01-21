from .config import AgentState, llm

def node_answer_normal(state: AgentState) -> AgentState:
    state['answer'] = llm.invoke(state["new_query"]).content
    return state