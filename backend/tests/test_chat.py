"""Giao thức SSE của /api/chat; graph được thay bằng bản giả (không gọi LLM)."""
from chatbot_haui.ai import graph as graph_module
from chatbot_haui.services import chat as chat_service


class FakeGraph:
    checkpointer = None

    def __init__(self, answer=None, error=None):
        self.answer, self.error = answer, error

    async def astream_events(self, inputs, config, version):
        assert inputs["ma_sv"] and inputs["user_key"] != inputs["ma_sv"]  # định danh gửi đi là HMAC
        assert "ho_ten" not in inputs["profile"] and "ma_sv" not in inputs["profile"]
        yield {"event": "on_chain_start", "name": "planner", "metadata": {"langgraph_node": "planner"}, "parent_ids": ["r"]}
        if self.error:
            raise self.error
        yield {"event": "on_chain_end", "name": "chatbot_turn", "metadata": {}, "parent_ids": [],
               "data": {"output": {"answer": self.answer}}}


def _events(client, headers, message):
    with client.stream("POST", "/api/chat", json={"message": message}, headers=headers) as response:
        return response.read().decode()


def test_chat_streams_status_then_answer_and_saves(client, auth_headers, monkeypatch):
    monkeypatch.setattr(chat_service, "get_graph", lambda: FakeGraph(answer="Bạn đủ điều kiện tham gia xét."))
    client.delete("/api/chat/messages", headers=auth_headers)

    body = _events(client, auth_headers, "học bổng?")
    assert body.index("event: status") < body.index('"delta": "Bạn đủ điều kiện tham gia xét."') < body.index("event: done")
    assert graph_module.STAGES["planner"] in body

    messages = client.get("/api/chat/messages", headers=auth_headers).json()
    assert [(m["role"], m["content"]) for m in messages] == [("user", "học bổng?"), ("bot", "Bạn đủ điều kiện tham gia xét.")]


def test_chat_error_event_hides_details(client, auth_headers, monkeypatch):
    monkeypatch.setattr(chat_service, "get_graph", lambda: FakeGraph(error=RuntimeError("column x does not exist")))
    body = _events(client, auth_headers, "x")
    assert "event: error" in body and "column" not in body


def test_clear_messages(client, auth_headers):
    assert client.delete("/api/chat/messages", headers=auth_headers).status_code == 204
    assert client.get("/api/chat/messages", headers=auth_headers).json() == []
