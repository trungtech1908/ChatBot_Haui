"""API chat: cuộc trò chuyện và giao thức SSE; graph được thay bằng bản giả (không gọi LLM)."""
import json
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from langchain_core.messages import AIMessageChunk
from sqlalchemy import text

from chatbot_haui.db.session import engine
from chatbot_haui.services import chat as chat_service

OTHER = "2023654041"


class FakeCheckpointer:
    def __init__(self):
        self.deleted: list[str] = []

    async def adelete_thread(self, thread_id):
        self.deleted.append(thread_id)


class FakeGraph:
    def __init__(self, answer="Trả lời.", error=None):
        self.answer, self.error = answer, error
        self.checkpointer = FakeCheckpointer()
        self.threads: list[str] = []

    async def astream_events(self, inputs, config, version):
        assert inputs["ma_sv"] and inputs["user_key"] != inputs["ma_sv"]  # định danh gửi đi là HMAC
        assert "ho_ten" not in inputs["profile"] and "ma_sv" not in inputs["profile"]
        self.threads.append(config["configurable"]["thread_id"])
        yield {"event": "on_chain_start", "name": "planner", "metadata": {"langgraph_node": "planner"}, "parent_ids": ["r"]}
        if self.error:
            raise self.error
        yield {"event": "on_chain_start", "name": "generator", "metadata": {"langgraph_node": "generator"}, "parent_ids": ["r"]}
        for token in ("Bản ", "nháp"):
            yield {"event": "on_chat_model_stream", "name": "Fake", "metadata": {"langgraph_node": "generator"},
                   "parent_ids": ["r"], "data": {"chunk": AIMessageChunk(content=token)}}
        yield {"event": "on_chain_end", "name": "chatbot_turn", "metadata": {}, "parent_ids": [],
               "data": {"output": {"answer": self.answer}}}


@pytest.fixture
def graph(monkeypatch):
    g = FakeGraph()
    monkeypatch.setattr(chat_service, "get_graph", lambda: g)
    return g


@pytest.fixture
def other_headers(client):
    token = client.post("/api/auth/login", json={"username": OTHER, "password": OTHER}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _send(client, headers, message, conversation_id=None):
    body = {"message": message} | ({"conversationId": conversation_id} if conversation_id else {})
    with client.stream("POST", "/api/chat", json=body, headers=headers) as response:
        body = response.read().decode()
        return response.status_code, (_parse(body) if response.status_code == 200 else json.loads(body))


def _parse(body):
    """[(event, data)] theo thứ tự nhận."""
    out = []
    for block in body.strip().split("\n\n"):
        if not block:
            continue
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        out.append((lines.get("event", "message"), json.loads(lines["data"])))
    return out


def _start(client, headers, message="học bổng?"):
    """Gửi câu hỏi đầu tiên → id cuộc trò chuyện mới."""
    _, events = _send(client, headers, message)
    return events[0][1]["id"]


def test_first_message_creates_conversation_then_streams(client, auth_headers, graph):
    client.delete("/api/chat/conversations", headers=auth_headers)
    graph.answer = "Bạn đủ điều kiện tham gia xét."
    status, events = _send(client, auth_headers, "  Điều kiện\nhọc bổng KKHT?  ")

    assert status == 200
    assert [e for e, _ in events] == ["conversation", "step", "step", "delta", "delta", "answer", "done"]
    conv = events[0][1]
    assert conv["title"] == "Điều kiện học bổng KKHT?"
    assert events[1][1] == {"id": "plan-1", "label": "Xác định cần tra cứu những gì", "status": "running", "detail": ""}
    assert [d["text"] for e, d in events if e == "delta"] == ["Bản ", "nháp"]  # token nháp đến trước câu cuối
    assert events[5][1] == {"text": "Bạn đủ điều kiện tham gia xét."}
    assert graph.threads == [conv["id"]]  # bộ nhớ phiên của graph theo cuộc trò chuyện

    listed = client.get("/api/chat/conversations", headers=auth_headers).json()
    assert [c["id"] for c in listed] == [conv["id"]]
    messages = client.get(f"/api/chat/conversations/{conv['id']}/messages", headers=auth_headers).json()
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "  Điều kiện\nhọc bổng KKHT?  "), ("bot", "Bạn đủ điều kiện tham gia xét.")]


def test_follow_up_stays_in_same_conversation_and_thread(client, auth_headers, graph):
    first = _start(client, auth_headers)
    status, events = _send(client, auth_headers, "còn hạn nộp hồ sơ?", first)
    assert status == 200 and events[0][0] != "conversation"
    assert graph.threads == [first, first]
    messages = client.get(f"/api/chat/conversations/{first}/messages", headers=auth_headers).json()
    assert [m["content"] for m in messages if m["role"] == "user"] == ["học bổng?", "còn hạn nộp hồ sơ?"]


def test_conversations_are_separate_and_most_recent_first(client, auth_headers, graph):
    client.delete("/api/chat/conversations", headers=auth_headers)
    a = _start(client, auth_headers, "câu A")
    b = _start(client, auth_headers, "câu B")
    assert a != b and graph.threads == [a, b]
    assert [c["id"] for c in client.get("/api/chat/conversations", headers=auth_headers).json()] == [b, a]

    _send(client, auth_headers, "hỏi tiếp A", a)  # hoạt động mới đưa A lên đầu
    assert [c["id"] for c in client.get("/api/chat/conversations", headers=auth_headers).json()] == [a, b]
    b_messages = client.get(f"/api/chat/conversations/{b}/messages", headers=auth_headers).json()
    assert [m["content"] for m in b_messages if m["role"] == "user"] == ["câu B"]


def test_other_students_conversation_is_not_found(client, auth_headers, other_headers, graph):
    mine = _start(client, auth_headers)
    assert client.get(f"/api/chat/conversations/{mine}/messages", headers=other_headers).status_code == 404
    assert client.patch(f"/api/chat/conversations/{mine}", json={"title": "x"}, headers=other_headers).status_code == 404
    assert client.delete(f"/api/chat/conversations/{mine}", headers=other_headers).status_code == 404
    status, _ = _send(client, other_headers, "chen vào", mine)
    assert status == 404 and graph.threads == [mine]  # không chạy graph trên thread của người khác
    assert mine not in [c["id"] for c in client.get("/api/chat/conversations", headers=other_headers).json()]
    assert client.get(f"/api/chat/conversations/{mine}/messages", headers=auth_headers).status_code == 200


def test_unknown_conversation_id_is_404(client, auth_headers, graph):
    status, _ = _send(client, auth_headers, "x", "00000000-0000-0000-0000-000000000000")
    assert status == 404 and graph.threads == []


def test_rename_conversation(client, auth_headers, graph):
    conv = _start(client, auth_headers)
    r = client.patch(f"/api/chat/conversations/{conv}", json={"title": "  Học   bổng kỳ 2 "}, headers=auth_headers)
    assert r.status_code == 200 and r.json()["title"] == "Học bổng kỳ 2"
    assert client.patch(f"/api/chat/conversations/{conv}", json={"title": "   "}, headers=auth_headers).status_code == 422
    assert client.patch(f"/api/chat/conversations/{conv}", json={"title": "x" * 121}, headers=auth_headers).status_code == 422


def test_delete_conversation_removes_messages_and_graph_memory(client, auth_headers, graph):
    keep = _start(client, auth_headers, "giữ lại")
    drop = _start(client, auth_headers, "xóa đi")
    assert client.delete(f"/api/chat/conversations/{drop}", headers=auth_headers).status_code == 204
    assert graph.checkpointer.deleted == [drop]
    assert client.get(f"/api/chat/conversations/{drop}/messages", headers=auth_headers).status_code == 404
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM chat_message WHERE conversation_id = :c"), {"c": drop}).scalar() == 0
    assert client.get(f"/api/chat/conversations/{keep}/messages", headers=auth_headers).status_code == 200


def test_delete_all_only_touches_own_conversations(client, auth_headers, other_headers, graph):
    mine = _start(client, auth_headers)
    theirs = _start(client, other_headers)
    assert client.delete("/api/chat/conversations", headers=auth_headers).status_code == 204
    assert client.get("/api/chat/conversations", headers=auth_headers).json() == []
    assert mine in graph.checkpointer.deleted and theirs not in graph.checkpointer.deleted
    assert theirs in [c["id"] for c in client.get("/api/chat/conversations", headers=other_headers).json()]


def test_chat_error_event_hides_details(client, auth_headers, graph):
    graph.error = RuntimeError("column x does not exist")
    _, events = _send(client, auth_headers, "x")
    assert events[-1][0] == "error" and "column" not in json.dumps(events)


@pytest.mark.parametrize("message, title", [
    ("Học bổng?", "Học bổng?"),
    ("  a\n\n b\t c ", "a b c"),
    ("x" * 80, "x" * 60 + "…"),  # không có khoảng trắng: cắt cứng
    ("điều kiện " * 10, "điều kiện điều kiện điều kiện điều kiện điều kiện điều kiện…"),  # cắt ở ranh giới từ
    ("   ", "Cuộc trò chuyện mới"),
])
def test_make_title(message, title):
    assert chat_service.make_title(message) == title
    assert len(chat_service.make_title(message)) <= chat_service.TITLE_LEN + 1


def test_migration_moves_old_history_and_graph_memory_into_one_conversation(client):
    """Lịch sử trước khi có cuộc trò chuyện: mỗi tài khoản → một cuộc, checkpoint thread_id=username chuyển theo."""
    cfg = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.downgrade(cfg, "c996469711a7")
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM chat_message"))
            conn.execute(text("""INSERT INTO chat_message (username, role, content, created_at) VALUES
                (:u, 'bot', 'lời chào', '2026-09-01 08:00'), (:u, 'user', 'Câu hỏi đầu tiên', '2026-09-01 08:01'),
                (:u, 'bot', 'trả lời', '2026-09-02 09:00'), (:o, 'user', 'của người khác', '2026-09-03 10:00')"""),
                {"u": OTHER, "o": "2024619567"})
            conn.execute(text("""INSERT INTO checkpoints (thread_id, checkpoint_ns, checkpoint_id, checkpoint, metadata)
                VALUES (:u, '', 'mig-test', '{}', '{}')"""), {"u": OTHER})
    finally:
        command.upgrade(cfg, "head")

    with engine.connect() as conn:
        convs = conn.execute(text("SELECT id, username, title, created_at, updated_at FROM chat_conversation ORDER BY username")).all()
        assert [(c.username, c.title) for c in convs] == [("2023654041", "Câu hỏi đầu tiên"), ("2024619567", "của người khác")]
        mine = convs[0]
        assert (str(mine.created_at), str(mine.updated_at)) == ("2026-09-01 08:00:00", "2026-09-02 09:00:00")
        assert conn.execute(text("SELECT count(*) FROM chat_message WHERE conversation_id = :c"), {"c": mine.id}).scalar() == 3
        threads = conn.execute(text("SELECT thread_id FROM checkpoints WHERE checkpoint_id = 'mig-test'")).scalars().all()
        assert threads == [mine.id]
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM checkpoints WHERE checkpoint_id = 'mig-test'"))
