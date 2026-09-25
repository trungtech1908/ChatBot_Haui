"""Đồ thị Planner–Executor (ARCHITECTURE mục 1, 3).

  rewriter → router ─┬─ (chitchat | out_of_scope | da_co_trong_lich_su) → direct ─────────────────┐
                     └─ can_tra_cuu → memory_read → planner ─┬─ không có bước → fallback ─────────┤
                                                             └─ executor → aggregator ─┬─ rỗng → fallback
                                                                                       └─ generator → validator
     validator: OK → finalize | THIEU_BANG_CHUNG (1 lần) → planner | KHANG_DINH_SAI (1 lần) → generator
                | còn lại → fallback                                                                   │
  fallback → finalize → END                                                                           ◄┘

Bộ nhớ phiên (history 6 lượt + summary) nằm trong state, được checkpointer Postgres giữ theo thread.
Memory Write chạy nền SAU khi đã trả lời (services/chat.py), không nằm trong graph.
"""
import asyncio
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy import text

from chatbot_haui.ai.nodes.answering import aggregator, fallback, generator, validator
from chatbot_haui.ai.nodes.conversation import direct, finalize, rewriter, router
from chatbot_haui.ai.nodes.executor import executor
from chatbot_haui.ai.nodes.planning import memory_read, planner
from chatbot_haui.ai.state import AgentState
from chatbot_haui.db.session import chatbot_scope

MAX_REPLAN = 1
MAX_REGEN = 1

# Trạng thái hiển thị cho người dùng khi node bắt đầu chạy
STAGES = {
    "rewriter": "Đang đọc câu hỏi…",
    "planner": "Đang lập kế hoạch tra cứu…",
    "executor": "Đang tra cứu quy chế và dữ liệu…",
    "generator": "Đang soạn câu trả lời…",
    "validator": "Đang kiểm tra câu trả lời…",
}
# Trường "từng lượt": checkpointer giữ state giữa các lượt nên phải đặt lại mỗi lần hỏi
_TURN_RESET: dict[str, Any] = {
    "query_rewritten": "", "route": "can_tra_cuu", "reuse_turn": None, "memories": [], "plan": {}, "results": {},
    "evidence": [], "missing": [], "draft": "", "verdict": {}, "replan_count": 0, "regen_count": 0,
    "fallback_reason": "", "answer": "",
}


def after_router(state: AgentState) -> str:
    return "memory_read" if state["route"] == "can_tra_cuu" else "direct"


def after_planner(state: AgentState) -> str:
    return "executor" if (state.get("plan") or {}).get("new_steps") else "fallback"


def after_aggregator(state: AgentState) -> str:
    return "generator" if state.get("evidence") else "fallback"


def after_validator(state: AgentState) -> str:
    verdict = (state.get("verdict") or {}).get("verdict")
    if verdict == "OK":
        return "finalize"
    if verdict == "THIEU_BANG_CHUNG" and state.get("replan_count", 0) < MAX_REPLAN:
        return "planner"
    if verdict == "KHANG_DINH_SAI" and state.get("regen_count", 0) < MAX_REGEN:
        return "generator"
    return "fallback"


def build_graph(checkpointer=None) -> CompiledStateGraph:
    g = StateGraph(AgentState)
    for name, fn in [
        ("rewriter", rewriter), ("router", router), ("direct", direct), ("memory_read", memory_read),
        ("planner", planner), ("executor", executor), ("aggregator", aggregator), ("generator", generator),
        ("validator", validator), ("fallback", fallback), ("finalize", finalize),
    ]:
        g.add_node(name, fn)

    g.add_edge(START, "rewriter")
    g.add_edge("rewriter", "router")
    g.add_conditional_edges("router", after_router, ["direct", "memory_read"])
    g.add_edge("direct", "finalize")
    g.add_edge("memory_read", "planner")
    g.add_conditional_edges("planner", after_planner, ["executor", "fallback"])
    g.add_edge("executor", "aggregator")
    g.add_conditional_edges("aggregator", after_aggregator, ["generator", "fallback"])
    g.add_edge("generator", "validator")
    g.add_conditional_edges("validator", after_validator, ["finalize", "planner", "generator", "fallback"])
    g.add_edge("fallback", "finalize")
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)


_graph: CompiledStateGraph | None = None


def init_graph(checkpointer=None) -> CompiledStateGraph:
    global _graph
    _graph = build_graph(checkpointer)
    return _graph


def get_graph() -> CompiledStateGraph:
    return _graph if _graph is not None else init_graph()


def _load_profile_sync(ma_sv: str) -> dict:
    with chatbot_scope(ma_sv) as conn:
        row = conn.execute(text("SELECT * FROM chatbot.v_sinh_vien")).mappings().first()
    # Không đưa định danh vào prompt (ARCHITECTURE mục 2.1, 6)
    return {k: v for k, v in (row or {}).items() if k not in ("ma_sv", "ho_ten")}


async def load_profile(ma_sv: str) -> dict:
    """Hồ sơ học vụ đọc mới mỗi lượt: rẻ, và DB luôn là nguồn mới nhất."""
    return await asyncio.to_thread(_load_profile_sync, ma_sv)


def turn_input(query: str, ma_sv: str, user_key: str, profile: dict) -> dict:
    return {**_TURN_RESET, "query": query, "ma_sv": ma_sv, "user_key": user_key, "profile": profile}
