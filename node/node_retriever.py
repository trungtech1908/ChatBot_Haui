from .config import AgentState, client
from FlagEmbedding import BGEM3FlagModel
from qdrant_client.models import MatchAny, Filter, FieldCondition
from cohere import ClientV2
from dotenv import load_dotenv
import os

load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
co = ClientV2(COHERE_API_KEY)
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True, devices='cpu')

def node_retriever(state: AgentState) -> AgentState:
    embeddings = model.encode(
        [state['new_query']],
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False
    )
    query_vec = embeddings['dense_vecs'][0].tolist()

    filter_points = client.query_points(
        collection_name='RAG_ChatBot_HAUI_v1',
        query=query_vec,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key='source',
                    match=MatchAny(any=state['category'])
                )
            ]
        ),
        limit=30
    )

    docs = [p.payload.get('raw_text') for p in filter_points.points]

    if docs:
        results = co.rerank(
            model='rerank-v3.5',  # model rerank của Cohere
            query=state['new_query'],
            documents=docs, top_n=10
        )
        sorted_results = sorted(
            results.results,
            key=lambda x: x.relevance_score,  # sắp xếp theo score
            reverse=True  # giảm dần
        )
        state['retriever'] = [docs[r.index] for r in sorted_results]

    else:
        state['retriever'] = ['']
    return state