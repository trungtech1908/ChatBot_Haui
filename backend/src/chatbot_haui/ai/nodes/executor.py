"""Executor (ARCHITECTURE mục 2.5): code thuần, không phải LLM.

Sắp xếp topo theo depends_on, chạy song song các bước cùng tầng, thay tham chiếu {sN} / {sN.cot}
bằng kết quả thật. Bước lỗi ghi status=error và chạy tiếp; bước phụ thuộc vào bước lỗi thì bỏ qua.
Validator sẽ quyết định có lập lại kế hoạch hay không.

Timeout tính cả thời gian gọi LLM bên trong tool (Text2SQL sinh + sửa SQL, RAG tự đánh giá), nên dài hơn
statement_timeout 5s của DB.
"""
import asyncio
import logging
import re

from chatbot_haui.ai.state import AgentState, StepResult
from chatbot_haui.ai.tools.compute import ComputeError, evaluate
from chatbot_haui.ai.tools.rag import run_rag
from chatbot_haui.ai.tools.text2sql import run_sql

logger = logging.getLogger(__name__)

TIMEOUT = {"rag": 45.0, "sql": 45.0, "compute": 1.0}
_REF = re.compile(r"\{(s\d+)(?:\.(\w+))?\}")
MAX_REF_VALUES = 10


def _column_values(result: StepResult, column: str) -> list:
    rows = (result.get("output") or {}).get("rows") or []
    values = []
    for r in rows:
        v = r.get(column)
        if v is not None and v not in values:
            values.append(v)
    return values[:MAX_REF_VALUES]


def _summary(result: StepResult) -> str:
    out = result.get("output") or {}
    if result["tool"] == "sql":
        rows = out.get("rows") or []
        return "; ".join(", ".join(f"{k}={v}" for k, v in r.items()) for r in rows[:5]) or "không có dữ liệu"
    if result["tool"] == "rag":
        return ", ".join(dict.fromkeys(c["title"] for c in out.get("chunks", [])))
    return str(out.get("ket_qua", ""))


def substitute(text: str, results: dict[str, StepResult]) -> str:
    def repl(m: re.Match) -> str:
        sid, column = m.group(1), m.group(2)
        result = results.get(sid)
        if not result or result.get("status") != "ok":
            return m.group(0)
        if column:
            return ", ".join(str(v) for v in _column_values(result, column)) or "(không có)"
        return _summary(result)
    return _REF.sub(repl, text)


def _bind(bien: dict[str, str], results: dict[str, StepResult]) -> dict[str, float]:
    """Biến compute: 'sN.cot' → giá trị cột ở dòng đầu kết quả sql sN; hoặc một số."""
    values = {}
    for name, ref in bien.items():
        ref = str(ref).strip()
        m = re.fullmatch(r"(s\d+)\.(\w+)", ref)
        if m:
            rows = ((results.get(m.group(1)) or {}).get("output") or {}).get("rows") or []
            if not rows or m.group(2) not in rows[0]:
                raise ComputeError(f"Không lấy được {ref}")
            value = rows[0][m.group(2)]
        else:
            value = ref.replace(",", ".")
        try:
            values[name] = float(value)
        except (TypeError, ValueError) as e:
            raise ComputeError(f"Giá trị của {name} không phải số: {value!r}") from e
    return values


async def _run(step: dict, results: dict[str, StepResult], ma_sv: str) -> StepResult:
    tool = step["tool"]
    base = StepResult(tool=tool, purpose=step.get("purpose", ""))
    failed = [d for d in step["depends_on"] if results.get(d, {}).get("status") != "ok"]
    if failed:
        return {**base, "status": "skipped", "error": f"bước phụ thuộc không thành công: {', '.join(failed)}"}
    try:
        if tool == "rag":
            query = substitute(step["query"], results)
            output = await asyncio.wait_for(run_rag(query, step.get("van_ban")), TIMEOUT[tool])
            return {**base, "status": "ok", "output": output}
        if tool == "sql":
            question = substitute(step["query"], results)
            output = await asyncio.wait_for(run_sql(question, ma_sv), TIMEOUT[tool])
            output["question"] = question
            if output.get("unsupported"):
                return {**base, "status": "unsupported", "output": output}
            return {**base, "status": "ok", "output": output}
        variables = _bind(step.get("bien") or {}, results)
        value = evaluate(step["expr"], variables)
        return {**base, "status": "ok", "output": {"expr": step["expr"], "bien": variables, "ket_qua": value}}
    except TimeoutError:
        logger.warning("Bước %s (%s) quá thời gian", step["id"], tool)
        return {**base, "status": "error", "error": "quá thời gian"}
    except Exception as e:
        logger.exception("Bước %s (%s) lỗi", step["id"], tool)
        return {**base, "status": "error", "error": str(e)[:300]}


async def executor(state: AgentState) -> dict:
    results: dict[str, StepResult] = dict(state.get("results") or {})
    pending = [s for s in state["plan"]["steps"] if s["id"] not in results]
    while pending:
        ready = [s for s in pending if all(d in results for d in s["depends_on"])]
        if not ready:  # phụ thuộc vòng hoặc trỏ tới bước không chạy
            for s in pending:
                results[s["id"]] = StepResult(tool=s["tool"], purpose=s.get("purpose", ""), status="skipped",
                                              error="phụ thuộc không giải được")
            break
        outputs = await asyncio.gather(*(_run(s, results, state["ma_sv"]) for s in ready))
        for s, r in zip(ready, outputs):
            results[s["id"]] = r
        pending = [s for s in pending if s["id"] not in results]
    return {"results": results}
