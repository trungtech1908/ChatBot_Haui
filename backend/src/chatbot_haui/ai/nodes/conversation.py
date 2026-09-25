"""Query Rewriter, Router, Direct Responder, Finalize (ARCHITECTURE mục 2.2, 2.3, 2.10 — bộ nhớ phiên)."""
from datetime import datetime, timedelta
from functools import lru_cache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from chatbot_haui.ai.llm import structured, text
from chatbot_haui.ai.prompts import conversation as prompts
from chatbot_haui.ai.state import AgentState, Route, Turn

MAX_TURNS = 6  # số lượt gần nhất giữ nguyên văn; cũ hơn thì gộp vào tóm tắt
SESSION_GAP = timedelta(minutes=30)  # hai lượt cách nhau quá mức này coi là khác phiên
ANSWER_PREVIEW = 800  # cắt câu trả lời cũ khi đưa vào prompt cho gọn


def _chain(system: str, human: str, size="small"):
    return ChatPromptTemplate.from_messages([("system", system), ("human", human)]) | text(size)


@lru_cache
def _rewriter():
    return _chain(prompts.REWRITE_SYSTEM, prompts.REWRITE_HUMAN) | StrOutputParser()


class RouteDecision(BaseModel):
    route: Route
    reuse_turn: int | None = Field(default=None, description="Số thứ tự lượt được dùng lại khi route = da_co_trong_lich_su")


@lru_cache
def _router():
    return ChatPromptTemplate.from_messages([
        ("system", prompts.ROUTER_SYSTEM), ("human", prompts.ROUTER_HUMAN),
    ]) | structured("small", RouteDecision)


@lru_cache
def _direct():
    return _chain(prompts.DIRECT_SYSTEM, prompts.DIRECT_HUMAN) | StrOutputParser()


@lru_cache
def _summarizer():
    return _chain(prompts.SUMMARY_SYSTEM, prompts.SUMMARY_HUMAN) | StrOutputParser()


def render_turns(turns: list[tuple[int, Turn]]) -> str:
    return "\n\n".join(
        f"Lượt {i}\nSinh viên: {t['user']}\nTrợ lý: {t['assistant'][:ANSWER_PREVIEW]}" for i, t in turns
    ) or "(không có)"


def session_turns(history: list[Turn], now: datetime) -> list[tuple[int, Turn]]:
    """Các lượt thuộc phiên hiện tại: chuỗi lượt liên tiếp gần nhất, mỗi lượt cách lượt sau không quá SESSION_GAP.

    Chỉ các lượt này mới được dùng lại nguyên câu trả lời (ARCHITECTURE 2.3: không dùng lại số liệu cá nhân giữa các phiên).
    """
    out, later = [], now
    for i in range(len(history), 0, -1):
        at = datetime.fromisoformat(history[i - 1]["at"])
        if later - at > SESSION_GAP:
            break
        out.append((i, history[i - 1]))
        later = at
    return out[::-1]


async def rewriter(state: AgentState, config: RunnableConfig) -> dict:
    history = state.get("history") or []
    if not history:  # câu đầu tiên luôn tự đứng được: bỏ qua 1 lần gọi LLM
        return {"query_rewritten": state["query"]}
    text = await _rewriter().ainvoke({
        "summary": state.get("summary") or "(không có)",
        "history": render_turns(list(enumerate(history, 1))),
        "query": state["query"],
    }, config)
    return {"query_rewritten": text.strip() or state["query"]}


async def router(state: AgentState, config: RunnableConfig) -> dict:
    turns = session_turns(state.get("history") or [], datetime.now())
    decision: RouteDecision = await _router().ainvoke(
        {"session_turns": render_turns(turns), "query": state["query_rewritten"]}, config)
    route, reuse = decision.route, decision.reuse_turn
    if route == "da_co_trong_lich_su" and reuse not in {i for i, _ in turns}:
        route, reuse = "can_tra_cuu", None  # chỉ số không hợp lệ / ngoài phiên → tra cứu lại cho chắc
    return {"route": route, "reuse_turn": reuse}


async def direct(state: AgentState, config: RunnableConfig) -> dict:
    if state["route"] == "da_co_trong_lich_su":
        return {"answer": state["history"][state["reuse_turn"] - 1]["assistant"]}
    answer = await _direct().ainvoke({"query": state["query"], "memories": "(không có)"}, config)
    return {"answer": answer.strip()}


async def finalize(state: AgentState, config: RunnableConfig) -> dict:
    """Ghi lượt vừa xong vào bộ nhớ phiên; lượt cũ nhất vượt quá MAX_TURNS được gộp vào tóm tắt cuộn."""
    history = list(state.get("history") or [])
    history.append(Turn(user=state["query"], assistant=state["answer"], at=datetime.now().isoformat(timespec="seconds")))
    summary = state.get("summary") or ""
    while len(history) > MAX_TURNS:
        old = history.pop(0)
        summary = (await _summarizer().ainvoke({
            "summary": summary or "(chưa có)", "user": old["user"], "assistant": old["assistant"][:ANSWER_PREVIEW],
        }, config)).strip()
    return {"history": history, "summary": summary}
