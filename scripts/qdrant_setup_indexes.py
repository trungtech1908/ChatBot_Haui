import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType


def main() -> None:
    load_dotenv(".env")
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    if not url:
        raise RuntimeError("Missing QDRANT_URL in environment/.env")

    client = QdrantClient(url=url, api_key=api_key)
    collection_name = os.getenv("QDRANT_COLLECTION", "RAG_ChatBot_HAUI_v1")

    # Create payload index for filtering by source (keyword)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="source",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    print(f"OK: created/ensured payload index 'source' on collection '{collection_name}'")


if __name__ == "__main__":
    main()

