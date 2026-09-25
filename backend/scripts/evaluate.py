"""Đánh giá chatbot: chạy đúng graph của backend trên bộ câu hỏi có đáp án mẫu, LLM chấm điểm.

Chạy từ backend/:
    uv run --no-sync python scripts/evaluate.py ../haui_qa_dataset.json --limit 20 -o eval_results.json

File câu hỏi: [{"id", "question", "answer", "source": ["HocBong.pdf", ...], "answerable": bool}, ...]
(định dạng cũ [{"Question", "Answer"}] vẫn đọc được).

Mỗi câu chạy như lượt đầu của một hội thoại mới, đăng nhập bằng --student (mặc định SV khuyết tật K19 trong
dữ liệu mẫu). Câu hỏi có yếu tố cá nhân sẽ được trả lời bằng dữ liệu của SV đó.

Chỉ số:
  pass rate       LLM giám khảo so với đáp án mẫu (ARCHITECTURE mục 7: câu trả lời)
  doc recall      tỉ lệ văn bản nguồn của đáp án mẫu có trong các chunk RAG truy hồi được (mục 7: RAG)
Mỗi câu gọi LLM 5–8 lần; tôn trọng quota của provider (--limit).
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Literal

os.chdir(Path(__file__).resolve().parents[1])

from langchain_core.prompts import ChatPromptTemplate  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from chatbot_haui.ai import memory, observability  # noqa: E402
from chatbot_haui.ai.graph import build_graph, load_profile, turn_input  # noqa: E402
from chatbot_haui.ai.llm import structured  # noqa: E402
from chatbot_haui.ai.prompts import judge as judge_prompts  # noqa: E402


class JudgeResult(BaseModel):
    factual_alignment: int = Field(..., ge=1, le=5)
    missing_information: Literal["yes", "no"]
    contradiction: Literal["yes", "no"]
    final_verdict: Literal["pass", "fail"]
    reason: str


def load_items(path: Path) -> list[dict]:
    items = json.loads(path.read_text(encoding="utf-8"))
    return [{
        "id": x.get("id", str(i)),
        "question": x.get("question") or x["Question"],
        "answer": x.get("answer") or x["Answer"],
        "sources": [s.removesuffix(".pdf") for s in x.get("source", [])],
        "answerable": x.get("answerable", True),
    } for i, x in enumerate(items, 1)]


async def run_one(graph, judge, item: dict, ma_sv: str, profile: dict, tags: list[str]) -> dict:
    key = memory.user_key(ma_sv)
    config = {
        "configurable": {"thread_id": f"eval-{item['id']}"},
        "callbacks": observability.callbacks(),
        "metadata": observability.trace_metadata(key, session_id=f"eval-{item['id']}", tags=tags),
        "run_name": "evaluate",
    }
    state = await graph.ainvoke(turn_input(item["question"], ma_sv, key, profile), config)
    results = state.get("results") or {}
    retrieved = sorted({c["source"] for r in results.values() if r.get("tool") == "rag" and r.get("status") == "ok"
                        for c in r["output"]["chunks"]})
    verdict: JudgeResult = await judge.ainvoke(
        {"question": item["question"], "reference_answer": item["answer"], "rag_answer": state["answer"]})
    return {
        **item,
        "bot_answer": state["answer"],
        "route": state.get("route"),
        "tools": [r.get("tool") + ":" + r.get("status", "") for r in results.values()],
        "retrieved_sources": retrieved,
        "doc_recall": (len(set(item["sources"]) & set(retrieved)) / len(item["sources"])) if item["sources"] and retrieved else None,
        "fallback": state.get("fallback_reason") or None,
        "judge": verdict.model_dump(),
    }


async def main_async(args):
    items = load_items(args.questions)[args.offset:args.offset + args.limit if args.limit else None]
    graph = build_graph()
    judge = ChatPromptTemplate.from_messages([
        ("system", judge_prompts.SYSTEM_PROMPT), ("human", judge_prompts.HUMAN_PROMPT),
    ]) | structured("main", JudgeResult)
    profile = await load_profile(args.student)
    results = []
    for i, item in enumerate(items, 1):
        try:
            r = await run_one(graph, judge, item, args.student, profile, ["evaluate"])
        except Exception as e:  # một câu lỗi không làm hỏng cả lượt đánh giá
            r = {**item, "error": f"{type(e).__name__}: {str(e)[:300]}"}
        results.append(r)
        v = r.get("judge", {}).get("final_verdict", "error")
        print(f"[{i}/{len(items)}] {v:5} recall={r.get('doc_recall')} {item['question'][:70]}", flush=True)
    observability.flush()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("eval_results.json"))
    ap.add_argument("--student", default="2024619567", help="mã SV đăng nhập khi hỏi")
    ap.add_argument("--limit", type=int, default=0, help="số câu tối đa (0 = tất cả)")
    ap.add_argument("--offset", type=int, default=0)
    args = ap.parse_args()

    results = asyncio.run(main_async(args))
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    judged = [r for r in results if "judge" in r]
    passed = sum(r["judge"]["final_verdict"] == "pass" for r in judged)
    recalls = [r["doc_recall"] for r in judged if r.get("doc_recall") is not None]
    print(f"\nPASS: {passed}/{len(judged)} ({passed / len(judged) if judged else 0:.1%}); lỗi: {len(results) - len(judged)}")
    for flag, name in ((True, "answerable"), (False, "không trả lời được")):
        group = [r for r in judged if r["answerable"] is flag]
        if group:
            ok = sum(r["judge"]["final_verdict"] == "pass" for r in group)
            print(f"  {name}: {ok}/{len(group)}")
    if recalls:
        print(f"Doc recall TB (câu có chạy RAG): {sum(recalls) / len(recalls):.1%} trên {len(recalls)} câu")
    print(f"Kết quả chi tiết: {args.output}")
    sys.exit(0)


if __name__ == "__main__":
    main()
