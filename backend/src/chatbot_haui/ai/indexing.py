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


class QdrantCheckError(RuntimeError):
    """Cấu hình Qdrant sai; thông điệp nói rõ sai ở đâu (URL, key hay quyền)."""


def check_qdrant(client: QdrantClient, collection: str) -> bool:
    """Kiểm tra kết nối, API key và quyền ghi TRƯỚC khi làm việc tốn thời gian (OCR, embedding).

    Quyền ghi được thử bằng cách tạo rồi xóa một collection tạm. Trả về collection đích đã tồn tại chưa.
    """
    try:
        existing = {c.name for c in client.get_collections().collections}
    except Exception as e:
        text = str(e)
        if any(code in text for code in ("401", "403", "Unauthorized", "Forbidden")):
            raise QdrantCheckError("QDRANT_API_KEY sai hoặc đã bị thu hồi (Qdrant từ chối)") from None
        raise QdrantCheckError(
            f"Không kết nối được QDRANT_URL ({type(e).__name__}): kiểm tra URL và cluster còn chạy không") from None
    probe = "_ingest_kiem_tra_quyen_ghi"
    try:
        if client.collection_exists(probe):
            client.delete_collection(probe)
        client.create_collection(probe, vectors_config=models.VectorParams(size=4, distance=models.Distance.COSINE))
        client.delete_collection(probe)
    except Exception as e:
        raise QdrantCheckError(
            f"QDRANT_API_KEY đọc được nhưng không có quyền tạo/xóa collection ({type(e).__name__})") from None
    return collection in existing
