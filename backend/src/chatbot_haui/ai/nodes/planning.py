"""Memory Read và Planner (ARCHITECTURE mục 2.4, 2.10)."""
import json
import logging
from functools import lru_cache
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from chatbot_haui.ai import documents, memory
from chatbot_haui.ai.llm import structured
from chatbot_haui.ai.prompts import planner as prompts
from chatbot_haui.ai.state import AgentState

logger = logging.getLogger(__name__)

MAX_STEPS = 5


class Step(BaseModel):
    id: str = Field(description="s1, s2, ...")
    tool: Literal["rag", "sql", "compute"]
    query: str = Field(default="", description="rag: truy vấn tìm kiếm; sql: câu hỏi dữ liệu")
    van_ban: list[str] = Field(default_factory=list, description="rag: mã văn bản cần lọc")
    expr: str = Field(default="", description="compute: biểu thức")
    bien: dict[str, str] = Field(default_factory=dict, description="compute: tên biến → 'sN.ten_cot' hoặc số")
    depends_on: list[str] = Field(default_factory=list)
    purpose: str = ""


class Plan(BaseModel):
    steps: list[Step] = Field(default_factory=list)
    answer_focus: str = ""
    khong_ho_tro: Literal["", "nguoi_khac", "ngoai_pham_vi"] = Field(
        default="", description="Khi không tạo bước nào: nguoi_khac (dữ liệu người khác) hoặc ngoai_pham_vi")


@lru_cache
def _planner():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.SYSTEM), ("human", prompts.HUMAN)])
    return prompt | structured("main", Plan)


def question_text(state: AgentState) -> str:
    """Câu gốc + câu viết lại: phạm vi theo câu gốc, câu viết lại chỉ để giải tham chiếu.

    Rewriter là model nhỏ, có thể lỡ thu hẹp/mở rộng phạm vi; đưa cả câu gốc để model phía sau không phụ thuộc lỗi đó.
    """
    original, rewritten = state["query"], state.get("query_rewritten") or state["query"]
    if rewritten.strip() == original.strip():
        return f"Câu hỏi gốc: {original}"
    return f"Câu hỏi gốc: {original}\nCâu viết lại (giải tham chiếu theo hội thoại): {rewritten}"


def profile_text(profile: dict) -> str:
    return json.dumps(profile, ensure_ascii=False, default=str) if profile else "(không có)"


def _sanitize(plan: Plan, done: set[str]) -> list[dict]:
    """Chỉ giữ bước hợp lệ: id mới không trùng, phụ thuộc trỏ tới bước có thật; tối đa MAX_STEPS."""
    steps, ids = [], set(done)
    for step in plan.steps[:MAX_STEPS]:
        if step.id in ids:
            logger.warning("Planner: bỏ bước trùng id %s", step.id)
            continue
        if step.tool in ("rag", "sql") and not step.query.strip():
            continue
        if step.tool == "compute" and not step.expr.strip():
            continue
        data = step.model_dump()
        data["depends_on"] = [d for d in step.depends_on if d in ids or d in {s.id for s in plan.steps}]
        data["van_ban"] = [v for v in step.van_ban if v in documents.SOURCES]
        steps.append(data)
        ids.add(step.id)
    return steps


async def memory_read(state: AgentState) -> dict:
    return {"memories": await memory.recall(state["user_key"], state["query_rewritten"])}


def _done_summary(state: AgentState) -> str:
    lines = []
    for sid, r in (state.get("results") or {}).items():
        lines.append(f"- {sid} ({r['tool']}, {r['status']}): {r.get('purpose', '')}")
    return "\n".join(lines) or "(không có)"


async def planner(state: AgentState, config: RunnableConfig) -> dict:
    verdict = state.get("verdict") or {}
    replanning = verdict.get("verdict") == "THIEU_BANG_CHUNG"
    replan = prompts.REPLAN.format(
        missing="\n".join(f"- {m}" for m in verdict.get("thieu", [])) or "(không rõ)", done=_done_summary(state),
    ) if replanning else ""

    plan: Plan = await _planner().ainvoke({
        "catalog": documents.catalog(),
        "profile": profile_text(state.get("profile") or {}),
        "summary": state.get("summary") or "(không có)",
        "memories": "; ".join(state.get("memories") or []) or "(không có)",
        "replan": replan,
        "question": question_text(state),
    }, config)

    done = set(state.get("results") or {})
    steps = _sanitize(plan, done)
    old = (state.get("plan") or {}).get("steps", []) if replanning else []
    update = {
        "plan": {"steps": old + steps, "answer_focus": plan.answer_focus or (state.get("plan") or {}).get("answer_focus", ""),
                 "new_steps": [s["id"] for s in steps]},
    }
    if replanning:
        update["replan_count"] = state.get("replan_count", 0) + 1
    if not steps and plan.khong_ho_tro:
        update["fallback_reason"] = plan.khong_ho_tro
    return update
