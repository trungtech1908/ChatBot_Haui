import os

from cohere import ClientV2
from dotenv import load_dotenv
from qdrant_client.models import FieldCondition, Filter, MatchAny

from chatbot_haui.agent.state import (
    AgentState,
    ENABLE_EXTERNAL_RERANK,
    QDRANT_COLLECTION,
    qdrant_client,
)

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
_bge_model = None
_cohere_client = None


def _get_bge():
    global _bge_model
    if _bge_model is None:
        from FlagEmbedding import BGEM3FlagModel
        _bge_model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True, devices="cpu")
    return _bge_model


def _get_cohere():
    global _cohere_client
    if _cohere_client is None and COHERE_API_KEY:
        _cohere_client = ClientV2(COHERE_API_KEY)
    return _cohere_client


def node_retriever(state: AgentState) -> AgentState:
    categories = state.get("category") or []
    if not categories or categories[0] == "Không xác định":
        state["retriever"] = []
        return state

    model = _get_bge()
    embeddings = model.encode(
        [state["new_query"]],
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    query_vec = embeddings["dense_vecs"][0].tolist()

    filter_points = qdrant_client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vec,
        query_filter=Filter(
            must=[FieldCondition(key="source", match=MatchAny(any=categories))]
        ),
        limit=30,
    )

    docs = [p.payload.get("raw_text", "") for p in filter_points.points if p.payload]
    docs = [d for d in docs if d]

    if not docs:
        state["retriever"] = []
        return state

    if ENABLE_EXTERNAL_RERANK and _get_cohere():
        co = _get_cohere()
        results = co.rerank(
            model="rerank-v3.5",
            query=state["new_query"],
            documents=docs,
            top_n=10,
        )
        sorted_results = sorted(results.results, key=lambda x: x.relevance_score, reverse=True)
        state["retriever"] = [docs[r.index] for r in sorted_results]
    else:
        state["retriever"] = docs[:10]

    return state
