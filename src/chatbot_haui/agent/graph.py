"""
Agentic RAG — quy chế sinh viên HaUI
Luồng: Rewrite → Cần thông tin? → (Vector DB + CSDL) → Sinh câu trả lời → Kiểm tra chất lượng → (lặp / fallback)
"""

from langgraph.graph import END, START, StateGraph

from chatbot_haui.agent.nodes import (
    MAX_AGENT_ITERATIONS,
    AgentState,
    node_db_decide,
    node_db_query,
    node_fallback,
    node_generate,
    node_need_info,
    node_quality_check,
    node_query_transform,
    node_retriever,
    node_save_zep,
    node_source_select,
    node_zep_context,
)


def init_run(state: AgentState) -> AgentState:
    from chatbot_haui.auth.session import resolve_session_ids

    ma_sv, user_id, thread_id = resolve_session_ids(
        ma_sv=state.get("ma_sv"),
        thread_id=state.get("thread_id"),
    )
    state["ma_sv"] = ma_sv
    state["user_id"] = user_id
    state["thread_id"] = thread_id
    state.setdefault("iteration", 0)
    state["max_iterations"] = state.get("max_iterations") or MAX_AGENT_ITERATIONS
    state.setdefault("quality_ok", False)
    return state


def increment_iteration(state: AgentState) -> AgentState:
    state["iteration"] = state.get("iteration", 0) + 1
    return state


def route_need_retrieval(state: AgentState) -> str:
    if state.get("needs_retrieval"):
        return "retrieval"
    return "direct"


def route_quality(state: AgentState) -> str:
    if state.get("quality_ok"):
        return "accept"
    n = state.get("iteration", 0)
    cap = state.get("max_iterations", MAX_AGENT_ITERATIONS)
    if n + 1 >= cap:
        return "fallback"
    return "retry"


graph = StateGraph(AgentState)

graph.add_node("init_run", init_run)
graph.add_node("zep_context", node_zep_context)
graph.add_node("rewrite", node_query_transform)
graph.add_node("need_info", node_need_info)
graph.add_node("source_select", node_source_select)
graph.add_node("retriever", node_retriever)
graph.add_node("db_decide", node_db_decide)
graph.add_node("db_query", node_db_query)
graph.add_node("generate", node_generate)
graph.add_node("quality", node_quality_check)
graph.add_node("increment", increment_iteration)
graph.add_node("fallback", node_fallback)
graph.add_node("save_zep", node_save_zep)

graph.add_edge(START, "init_run")
graph.add_edge("init_run", "zep_context")
graph.add_edge("zep_context", "rewrite")
graph.add_edge("rewrite", "need_info")

graph.add_conditional_edges(
    "need_info",
    route_need_retrieval,
    {"retrieval": "source_select", "direct": "db_decide"},
)

graph.add_edge("source_select", "retriever")
graph.add_edge("retriever", "db_decide")
graph.add_edge("db_decide", "db_query")
graph.add_edge("db_query", "generate")
graph.add_edge("generate", "quality")

graph.add_conditional_edges(
    "quality",
    route_quality,
    {"accept": "save_zep", "retry": "increment", "fallback": "fallback"},
)

graph.add_edge("increment", "rewrite")
graph.add_edge("fallback", "save_zep")
graph.add_edge("save_zep", END)

app = graph.compile()


def run_agent(
    query: str,
    *,
    session=None,
    ma_sv: str | None = None,
    thread_id: str | None = None,
    ho_ten: str | None = None,
) -> AgentState:
    """
    Chạy một lượt hỏi đáp.

    Bắt buộc truyền `session` (sau đăng nhập) hoặc `ma_sv` từ API/UI.
    """
    from chatbot_haui.auth.session import resolve_session_ids

    if session is not None:
        ma, uid, tid = resolve_session_ids(session)
        ho_ten = ho_ten or session.ho_ten
    else:
        ma, uid, tid = resolve_session_ids(ma_sv=ma_sv, thread_id=thread_id)

    initial: AgentState = {
        "query": query,
        "ma_sv": ma,
        "user_id": uid,
        "thread_id": tid,
        "ho_ten": ho_ten,
    }
    return app.invoke(initial)
