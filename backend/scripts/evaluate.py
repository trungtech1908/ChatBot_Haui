"""Đánh giá RAG: chạy luồng chatbot_haui.ai.graph trên bộ câu hỏi mẫu, LLM chấm điểm, tính tỉ lệ pass.

Chạy từ backend/: uv run python scripts/evaluate.py <questions.json> [-o results.json]
File câu hỏi: [{"Question": "...", "Answer": "..."}, ...]
"""
import argparse
import asyncio
import json
from pathlib import Path
from typing import Literal

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from chatbot_haui.ai.graph import run
from chatbot_haui.ai.llm import create_llm
from chatbot_haui.ai.prompts import judge as judge_prompts


class JudgeResult(BaseModel):
    factual_alignment: int = Field(..., ge=1, le=5)
    missing_information: Literal["yes", "no"]
    extra_information: Literal["yes", "no"]
    contradiction: Literal["yes", "no"]
    semantic_equivalence: Literal["high", "medium", "low"]
    final_verdict: Literal["pass", "fail"]
    reason: str


parser = PydanticOutputParser(pydantic_object=JudgeResult)
prompt = ChatPromptTemplate.from_messages([("system", judge_prompts.SYSTEM_PROMPT), ("human", judge_prompts.HUMAN_PROMPT)])
judge = prompt | create_llm(temperature=0) | parser


async def evaluate(items: list[dict]) -> list[dict]:
    results = []
    for i, item in enumerate(items, start=1):
        state = await run(item["Question"])
        verdict = await judge.ainvoke({
            "reference_answer": item["Answer"],
            "rag_answer": state["answer"],
            "format_instructions": parser.get_format_instructions(),
        })
        results.append({
            "question": item["Question"],
            "category": state.get("category"),
            "reference_answer": item["Answer"],
            "rag_answer": state["answer"],
            "judge": verdict.model_dump(),
        })
        print(f"[{i}/{len(items)}] {verdict.final_verdict}")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("questions", type=Path)
    ap.add_argument("-o", "--output", type=Path, default=Path("eval_results.json"))
    args = ap.parse_args()

    items = json.loads(args.questions.read_text(encoding="utf-8"))
    results = asyncio.run(evaluate(items))
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    passed = sum(r["judge"]["final_verdict"] == "pass" for r in results)
    print(f"PASS: {passed}/{len(results)} ({passed / len(results) if results else 0:.2%})")


if __name__ == "__main__":
    main()
