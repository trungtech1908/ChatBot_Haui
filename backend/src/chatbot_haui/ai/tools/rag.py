"""Tool RAG (ARCHITECTURE mục 2.6).

Truy hồi hybrid: dense bge-m3 + sparse BM25, hợp nhất bằng Reciprocal Rank Fusion ngay trên Qdrant,
rerank bằng Cohere lấy top 5. Sau đó LLM nhỏ tự đánh giá "đủ để trả lời câu hỏi con chưa";
chưa đủ thì viết lại truy vấn và truy hồi thêm, tối đa 2 vòng đánh giá.

Chunk hiện tại chỉ có payload {source, raw_text} (chưa cắt theo Điều/Khoản), nên chỉ lọc được
theo văn bản và trích dẫn được ở mức tên văn bản.
"""
import asyncio
import logging
from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient, models

from chatbot_haui.ai import documents
from chatbot_haui.ai.embedding import embed
from chatbot_haui.ai.indexing import DENSE, SPARSE
from chatbot_haui.ai.llm import structured
from chatbot_haui.ai.prompts import rag_judge
from chatbot_haui.ai.tools.sparse import encode_query
from chatbot_haui.core.config import settings

logger = logging.getLogger(__name__)

CANDIDATES = 30  # số ứng viên mỗi nhánh trước khi fusion
TOP_N = 5
MAX_JUDGE_ROUNDS = 2


@lru_cache
def get_qdrant() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=30)


@lru_cache
def _cohere():
    from cohere import AsyncClientV2
    return AsyncClientV2(settings.cohere_api_key)


class Judgement(BaseModel):
    du: bool = Field(description="true nếu các đoạn trích đã đủ căn cứ để trả lời câu hỏi")
    thieu: str = Field(default="", description="nếu chưa đủ: còn thiếu thông tin gì")
    truy_van_moi: str = Field(default="", description="nếu chưa đủ: truy vấn mới để tìm phần còn thiếu")


@lru_cache
def _judge():
    prompt = ChatPromptTemplate.from_messages([("system", rag_judge.SYSTEM), ("human", rag_judge.HUMAN)])
    return prompt | structured("small", Judgement)


def _search(query: str, sources: list[str] | None) -> list[dict]:
    """Đồng bộ (embedding CPU + Qdrant HTTP)."""
    dense = embed([query])[0]
    indices, values = encode_query(query)
    query_filter = (
        models.Filter(must=[models.FieldCondition(key="source", match=models.MatchAny(any=sources))])
        if sources else None
    )
    points = get_qdrant().query_points(
        settings.qdrant_collection,
        prefetch=[
            models.Prefetch(query=dense, using=DENSE, limit=CANDIDATES, filter=query_filter),
            models.Prefetch(query=models.SparseVector(indices=indices, values=values), using=SPARSE,
                            limit=CANDIDATES, filter=query_filter),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=CANDIDATES,
        with_payload=True,
    ).points
    return [{"id": str(p.id), "text": p.payload["raw_text"], "source": p.payload["source"]} for p in points]


async def _rerank(query: str, chunks: list[dict]) -> list[dict]:
    if not chunks:
        return []
    result = await _cohere().rerank(
        model="rerank-v3.5", query=query, documents=[c["text"] for c in chunks], top_n=min(TOP_N, len(chunks)),
    )
    return [{**chunks[r.index], "score": round(r.relevance_score, 4)} for r in result.results]


async def _retrieve(query: str, sources: list[str] | None) -> list[dict]:
    chunks = await asyncio.to_thread(_search, query, sources)
    if not chunks and sources:
        # Planner lọc nhầm văn bản → tìm lại trên toàn bộ thay vì trả rỗng
        logger.info("RAG: lọc theo %s không có kết quả, tìm trên toàn bộ văn bản", sources)
        chunks = await asyncio.to_thread(_search, query, None)
    return chunks


def _format(chunks: list[dict]) -> str:
    return "\n\n".join(f"[{i}] ({documents.title(c['source'])})\n{c['text']}" for i, c in enumerate(chunks, 1))


async def run_rag(query: str, sources: list[str] | None = None) -> dict:
    valid = [s for s in (sources or []) if s in documents.SOURCES] or None
    candidates = await _retrieve(query, valid)
    top = await _rerank(query, candidates)
    queries = [query]

    for _ in range(MAX_JUDGE_ROUNDS):
        judgement: Judgement = await _judge().ainvoke({"question": query, "chunks": _format(top) or "(không có)"})
        if judgement.du or not judgement.truy_van_moi.strip() or judgement.truy_van_moi in queries:
            break
        new_query = judgement.truy_van_moi.strip()
        queries.append(new_query)
        seen = {c["id"] for c in candidates}
        candidates += [c for c in await _retrieve(new_query, valid) if c["id"] not in seen]
        # Luôn rerank theo câu hỏi gốc: truy vấn mới chỉ để mở rộng tập ứng viên
        top = await _rerank(query, candidates)

    return {
        "queries": queries,
        "sufficient": judgement.du,
        "chunks": [{"source": c["source"], "title": documents.title(c["source"]), "text": c["text"], "score": c["score"]}
                   for c in top],
    }
