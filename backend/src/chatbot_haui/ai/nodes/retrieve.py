from cohere import ClientV2
from FlagEmbedding import BGEM3FlagModel
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny

from chatbot_haui.ai.state import AgentState
from chatbot_haui.core.config import settings

qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
cohere = ClientV2(settings.cohere_api_key)
embedder = BGEM3FlagModel(settings.embedding_model, use_fp16=False, devices="cpu")


def retrieve(state: AgentState) -> dict:
    query = state["new_query"]
    query_vec = embedder.encode([query])["dense_vecs"][0].tolist()

    # Lọc theo tài liệu đã phân loại, lấy 30 ứng viên rồi rerank còn 10
    points = qdrant.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vec,
        query_filter=Filter(must=[FieldCondition(key="source", match=MatchAny(any=state["category"]))]),
        limit=30,
    ).points
    docs = [p.payload["raw_text"] for p in points]
    if not docs:
        return {"retriever": []}

    # Cohere trả kết quả đã sắp xếp theo relevance_score giảm dần
    reranked = cohere.rerank(model="rerank-v3.5", query=query, documents=docs, top_n=10)
    return {"retriever": [docs[r.index] for r in reranked.results]}
