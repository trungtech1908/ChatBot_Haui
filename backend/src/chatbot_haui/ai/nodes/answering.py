"""Aggregator, Generator, Validator, Fallback (ARCHITECTURE mục 2.9)."""
from datetime import date
from functools import lru_cache
from typing import Literal

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from chatbot_haui.ai.llm import structured, text
from chatbot_haui.ai.nodes.planning import profile_text, question_text
from chatbot_haui.ai.prompts import answer as prompts
from chatbot_haui.ai.state import AgentState, Evidence
from chatbot_haui.core.config import settings

MAX_CHUNK_CHARS = 3000  # một chunk quy chế trung bình ~850 token
DATA_SOURCE = "hệ thống dữ liệu của trường"


def data_as_of() -> str:
    return settings.data_as_of or date.today().strftime("%d/%m/%Y")


def _sql_content(output: dict) -> str:
    lines = [f"Câu hỏi dữ liệu: {output.get('question', '')}"]
    if output.get("gia_dinh"):
        lines.append(f"Cách hiểu đã dùng: {output['gia_dinh']}")
    rows = output.get("rows") or []
    if not rows:
        lines.append("Kết quả: không có dòng nào (rỗng — đây là thông tin hợp lệ).")
    else:
        lines.append(f"Kết quả ({len(rows)} dòng):")
        lines += ["- " + "; ".join(f"{k}: {v}" for k, v in r.items()) for r in rows]
    return "\n".join(lines)


def aggregator(state: AgentState) -> dict:
    """Gom kết quả các bước thành danh sách bằng chứng có nguồn; bước lỗi → danh sách 'chưa tra được'."""
    evidence: list[Evidence] = []
    missing: list[str] = []

    def add(source: str, content: str):
        evidence.append(Evidence(id=f"E{len(evidence) + 1}", source=source, content=content))

    for r in (state.get("results") or {}).values():
        out = r.get("output") or {}
        if r["status"] == "ok" and r["tool"] == "rag":
            for c in out.get("chunks", []):
                add(c["title"], c["text"][:MAX_CHUNK_CHARS])
        elif r["status"] == "ok" and r["tool"] == "sql":
            add("dữ liệu của sinh viên (" + ", ".join(f"chatbot.{v}" for v in out.get("views", [])) + ")",
                _sql_content(out))
        elif r["status"] == "ok" and r["tool"] == "compute":
            bien = ", ".join(f"{k} = {v:g}" for k, v in out["bien"].items())
            add("phép tính", f"{out['expr']} với {bien} → {out['ket_qua']}")
        elif r["status"] == "unsupported":
            reason = "dữ liệu của người khác" if out.get("unsupported") == "nguoi_khac" else "hệ thống không có dữ liệu này"
            missing.append(f"{r.get('purpose', '')} ({reason})")
        else:
            missing.append(r.get("purpose", "") or r["tool"])

    # Thời điểm dữ liệu là một bằng chứng: Generator phải nêu nó (ARCHITECTURE mục 8) và Validator phải thấy nó
    # trong bằng chứng, nếu không sẽ coi ngày đó là thông tin bịa và bác câu trả lời
    if any(e["source"].startswith("dữ liệu của sinh viên") for e in evidence):
        add(DATA_SOURCE, f"Dữ liệu học vụ, tài chính của sinh viên được cập nhật đến ngày {data_as_of()}.")

    update: dict = {"evidence": evidence, "missing": missing}
    if not evidence:
        others = any((r.get("output") or {}).get("unsupported") == "nguoi_khac"
                     for r in (state.get("results") or {}).values())
        update["fallback_reason"] = "nguoi_khac" if others else "khong_co_bang_chung"
    return update


def render_evidence(evidence: list[Evidence]) -> str:
    # Không in id (E1, E2...): model có xu hướng chép nhãn nội bộ vào câu trả lời
    return "\n\n".join(f"--- Nguồn: {e['source']}\n{e['content']}" for e in evidence)


@lru_cache
def _generator():
    return ChatPromptTemplate.from_messages([
        ("system", prompts.GENERATOR_SYSTEM), ("human", prompts.GENERATOR_HUMAN),
    ]) | text("main") | StrOutputParser()


async def generator(state: AgentState, config: RunnableConfig) -> dict:
    verdict = state.get("verdict") or {}
    fixing = verdict.get("verdict") == "KHANG_DINH_SAI"
    fix = prompts.GENERATOR_FIX.format(
        errors="\n".join(f"- {e}" for e in verdict.get("loi", [])), draft=state.get("draft", ""),
    ) if fixing else ""
    draft = await _generator().ainvoke({
        "memories": "; ".join(state.get("memories") or []) or "(không có)",
        "profile": profile_text(state.get("profile") or {}),
        "question": question_text(state),
        "answer_focus": (state.get("plan") or {}).get("answer_focus") or "(trả lời đúng câu hỏi)",
        "evidence": render_evidence(state.get("evidence") or []),
        "missing": "; ".join(state.get("missing") or []) or "(không có)",
        "fix": fix,
    }, config)
    update = {"draft": draft.strip()}
    if fixing:
        update["regen_count"] = state.get("regen_count", 0) + 1
    return update


class Verdict(BaseModel):
    verdict: Literal["OK", "THIEU_BANG_CHUNG", "KHANG_DINH_SAI", "KHONG_THE_TRA_LOI"]
    loi: list[str] = Field(default_factory=list, description="Các khẳng định sai hoặc không có trong bằng chứng")
    thieu: list[str] = Field(default_factory=list, description="Các ý của câu hỏi chưa được trả lời")


@lru_cache
def _validator():
    return ChatPromptTemplate.from_messages([
        ("system", prompts.VALIDATOR_SYSTEM), ("human", prompts.VALIDATOR_HUMAN),
    ]) | structured("main", Verdict)


async def validator(state: AgentState, config: RunnableConfig) -> dict:
    verdict: Verdict = await _validator().ainvoke({
        "question": question_text(state),
        "evidence": render_evidence(state.get("evidence") or []),
        "draft": state["draft"],
    }, config)
    update = {"verdict": verdict.model_dump()}
    if verdict.verdict == "OK":
        update["answer"] = state["draft"]
    return update


def fallback(state: AgentState) -> dict:
    reason = state.get("fallback_reason")
    return {"answer": prompts.FALLBACK_OTHER_PERSON if reason == "nguoi_khac" else prompts.FALLBACK}
