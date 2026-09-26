"""check_qdrant(): cấu hình Qdrant sai phải bị phát hiện TRƯỚC khi OCR, với lý do rõ ràng (client giả, không gọi mạng)."""
from types import SimpleNamespace

import pytest

from chatbot_haui.ai.indexing import QdrantCheckError, check_qdrant


class FakeClient:
    def __init__(self, list_error=None, create_error=None, existing=("RAG_ChatBot_HAUI",)):
        self.list_error, self.create_error, self.existing = list_error, create_error, existing
        self.created, self.deleted = [], []

    def get_collections(self):
        if self.list_error:
            raise self.list_error
        return SimpleNamespace(collections=[SimpleNamespace(name=n) for n in self.existing])

    def collection_exists(self, name):
        return False

    def create_collection(self, name, **_):
        if self.create_error:
            raise self.create_error
        self.created.append(name)

    def delete_collection(self, name):
        self.deleted.append(name)


def test_ok_and_probe_collection_cleaned_up():
    client = FakeClient()
    assert check_qdrant(client, "RAG_ChatBot_HAUI") is True
    assert check_qdrant(client, "chua_co") is False
    assert client.created == client.deleted  # collection thử quyền ghi luôn bị xóa


@pytest.mark.parametrize("error, reason", [
    (Exception("Unexpected Response: 401 (Unauthorized)"), "API_KEY sai"),
    (Exception("403 Forbidden"), "API_KEY sai"),
    (ConnectionError("Name or service not known"), "Không kết nối được QDRANT_URL"),
])
def test_bad_url_or_key(error, reason):
    with pytest.raises(QdrantCheckError, match=reason):
        check_qdrant(FakeClient(list_error=error), "RAG_ChatBot_HAUI")


def test_read_only_key():
    with pytest.raises(QdrantCheckError, match="không có quyền tạo/xóa"):
        check_qdrant(FakeClient(create_error=Exception("403 Forbidden")), "RAG_ChatBot_HAUI")
