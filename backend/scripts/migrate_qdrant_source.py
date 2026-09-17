"""Đổi payload `source` trên Qdrant từ "<tên tài liệu>.json" thành "<tên tài liệu>" (không cần OCR lại).

Chạy từ backend/ (cấu hình Qdrant trong .env):
    uv run python scripts/migrate_qdrant_source.py --dry-run   # chỉ xem sẽ đổi gì
    uv run python scripts/migrate_qdrant_source.py             # đổi thật

Chạy lại nhiều lần vẫn an toàn: điểm đã đổi thì bỏ qua.
"""
import argparse
import os
from collections import defaultdict
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])  # để đọc đúng .env dù chạy từ đâu

from qdrant_client import QdrantClient  # noqa: E402

from chatbot_haui.core.config import settings  # noqa: E402

SUFFIX = ".json"
SCROLL_LIMIT = 256
UPDATE_BATCH = 1000


def collect_renames(client: QdrantClient, collection: str) -> tuple[dict[str, list], int]:
    """Trả về {source mới: [id điểm]} cho các điểm còn đuôi .json, kèm tổng số điểm."""
    renames: dict[str, list] = defaultdict(list)
    total, offset = 0, None
    while True:
        points, offset = client.scroll(
            collection, limit=SCROLL_LIMIT, offset=offset, with_payload=["source"], with_vectors=False
        )
        for point in points:
            total += 1
            source = (point.payload or {}).get("source")
            if isinstance(source, str) and source.endswith(SUFFIX):
                renames[source.removesuffix(SUFFIX)].append(point.id)
        if offset is None:
            return renames, total


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--collection", default=settings.qdrant_collection, help="mặc định lấy QDRANT_COLLECTION")
    parser.add_argument("--dry-run", action="store_true", help="chỉ in ra, không ghi lên Qdrant")
    args = parser.parse_args()

    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    if not client.collection_exists(args.collection):
        raise SystemExit(f"Không có collection '{args.collection}' trên {settings.qdrant_url}")

    renames, total = collect_renames(client, args.collection)
    changed = sum(len(ids) for ids in renames.values())
    print(f"Collection '{args.collection}': {total} điểm, {changed} điểm cần đổi source")
    for source, ids in sorted(renames.items()):
        print(f"  {source}{SUFFIX} -> {source}  ({len(ids)} điểm)")

    if not changed or args.dry_run:
        print("Không ghi gì lên Qdrant." if args.dry_run else "Không có gì cần đổi.")
        return

    for source, ids in renames.items():
        for start in range(0, len(ids), UPDATE_BATCH):
            client.set_payload(args.collection, payload={"source": source}, points=ids[start:start + UPDATE_BATCH], wait=True)
    print(f"Đã đổi source cho {changed} điểm.")


if __name__ == "__main__":
    main()
