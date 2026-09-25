"""Cấu trúc collection văn bản quy chế trên Qdrant — dùng chung cho scripts/ingest.py (ghi) và tools/rag.py (đọc).

Mỗi chunk có 2 vector:
  dense — bge-m3, 1024 chiều, cosine (ngữ nghĩa)
  bm25  — sparse, phần TF của BM25; IDF do Qdrant tính (Modifier.IDF) (khớp chính xác cụm từ)
Payload: source (tên PDF không đuôi, có index), raw_text.
"""
from qdrant_client import QdrantClient, models

from chatbot_haui.ai.embedding import DIMS
from chatbot_haui.ai.tools.sparse import average_length, encode_document

DENSE, SPARSE = "dense", "bm25"


def recreate_collection(client: QdrantClient, name: str) -> None:
    """Xóa (nếu có) rồi tạo lại collection hybrid rỗng."""
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(
        name,
        vectors_config={DENSE: models.VectorParams(size=DIMS, distance=models.Distance.COSINE)},
        sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )
    client.create_payload_index(name, field_name="source", field_schema=models.PayloadSchemaType.KEYWORD)


def make_points(texts: list[str], sources: list[str], dense_vectors) -> list[models.PointStruct]:
    avg_len = average_length(texts)
    points = []
    for i, (text, source, dense) in enumerate(zip(texts, sources, dense_vectors)):
        indices, values = encode_document(text, avg_len)
        points.append(models.PointStruct(
            id=i,
            vector={DENSE: [float(x) for x in dense], SPARSE: models.SparseVector(indices=indices, values=values)},
            payload={"source": source, "raw_text": text},
        ))
    return points
