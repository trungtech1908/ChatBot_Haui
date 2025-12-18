import os
import json
from typing import Literal
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field


# =========================
# 1. LLM
# =========================
llm = ChatOllama(
    model="deepseek-r1:8b"
)


# =========================
# 2. Judge schema
# =========================
class RAGJudgeResult(BaseModel):
    factual_alignment: int = Field(..., ge=1, le=5)
    missing_information: Literal["yes", "no"]
    extra_information: Literal["yes", "no"]
    contradiction: Literal["yes", "no"]
    semantic_equivalence: Literal["high", "medium", "low"]
    final_verdict: Literal["pass", "fail"]
    reason: str


parser = PydanticOutputParser(pydantic_object=RAGJudgeResult)


# =========================
# 3. Prompt
# =========================
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
Bạn là LLM Judge chuyên đánh giá hệ thống RAG.

Bạn chỉ được so sánh hai câu trả lời đã cho.
Không tự bổ sung kiến thức ngoài.
Diễn đạt khác nhưng đúng ý vẫn được xem là đúng.
"""
    ),
    (
        "human",
        """
CÂU TRẢ LỜI MẪU (REFERENCE):
{reference_answer}

CÂU TRẢ LỜI CỦA RAG:
{rag_answer}

Trả kết quả đúng format:
{format_instructions}
"""
    )
])


chain = prompt | llm | parser


# =========================
# 4. Batch judge từ 2 thư mục
# =========================
REF_DIR = "Validation"
RAG_DIR = "Validation_RAG"
OUT_DIR = "Validation_JUDGE"

os.makedirs(OUT_DIR, exist_ok=True)


def load_json_as_dict(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["Question"]: item["Answer"] for item in data}


for filename in os.listdir(REF_DIR):
    if not filename.endswith(".json"):
        continue

    ref_path = os.path.join(REF_DIR, filename)
    rag_path = os.path.join(RAG_DIR, filename.replace(".json", "_RAG.json"))

    if not os.path.exists(rag_path):
        continue

    ref_data = load_json_as_dict(ref_path)
    rag_data = load_json_as_dict(rag_path)

    judge_results = []

    for question, ref_answer in ref_data.items():
        rag_answer = rag_data.get(question)
        if not rag_answer:
            continue

        judge: RAGJudgeResult = chain.invoke({
            "reference_answer": ref_answer,
            "rag_answer": rag_answer,
            "format_instructions": parser.get_format_instructions()
        })

        judge_results.append({
            "question": question,
            "reference_answer": ref_answer,
            "rag_answer": rag_answer,
            "judge": judge.model_dump()
        })

    out_name = filename.replace(".json", "_JUDGE.json")
    out_path = os.path.join(OUT_DIR, out_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(judge_results, f, ensure_ascii=False, indent=2)
