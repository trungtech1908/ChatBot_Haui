"""State dùng chung cho mọi node (ARCHITECTURE mục 3).

Checkpointer giữ state giữa các lượt theo thread (= tài khoản), nên các trường "từng lượt"
phải được đặt lại ở đầu mỗi lượt — xem graph.turn_input().
"""
from typing import Any, Literal, TypedDict

Route = Literal["chitchat", "out_of_scope", "da_co_trong_lich_su", "can_tra_cuu"]


class Turn(TypedDict):
    user: str
    assistant: str
    at: str  # ISO timestamp, để biết lượt nào cùng phiên


class StepResult(TypedDict, total=False):
    tool: str
    purpose: str
    status: Literal["ok", "error", "unsupported", "skipped"]
    output: Any
    error: str  # thông điệp nội bộ, không bao giờ trả cho người dùng


class Evidence(TypedDict):
    id: str  # E1, E2, ...
    source: str  # 'Quy định xét học bổng (QĐ 725/QĐ-ĐHCN)' | 'dữ liệu chatbot.v_xet_hb' | 'phép tính'
    content: str


class AgentState(TypedDict, total=False):
    # --- Từ session: KHÔNG đưa vào prompt ---
    ma_sv: str
    user_key: str  # HMAC(ma_sv): định danh cho memory và trace

    # --- Giữ qua các lượt (checkpointer) ---
    history: list[Turn]  # tối đa 6 lượt gần nhất
    summary: str  # tóm tắt cuộn các lượt cũ hơn

    # --- Từng lượt ---
    query: str
    profile: dict  # 1 dòng v_sinh_vien, đã bỏ ma_sv và ho_ten
    query_rewritten: str
    route: Route
    reuse_turn: int | None  # chỉ số lượt trong history khi route = da_co_trong_lich_su
    memories: list[str]
    plan: dict
    results: dict[str, StepResult]
    evidence: list[Evidence]
    missing: list[str]  # bước lỗi / không làm được, để Generator và Validator biết
    draft: str
    verdict: dict
    replan_count: int
    regen_count: int
    fallback_reason: str
    answer: str
