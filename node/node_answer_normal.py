from .config import AgentState, llm

def node_answer_normal(state:AgentState) -> AgentState:
    state['answer'] = llm.invoke(state['new_query']).content
    return state
# input_state = AgentState(query='1 + 1 = ?')
# res = node_answer_normal(input_state)
# print(res['answer'])