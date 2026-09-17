from chatbot_haui.services import chat as chat_service


def _events(client, headers, message):
    with client.stream("POST", "/api/chat", json={"message": message}, headers=headers) as response:
        return response.read().decode()


def test_chat_streams_and_saves(client, auth_headers, monkeypatch):
    async def fake_stream(query):
        yield "Xin "
        yield "chào"

    monkeypatch.setattr(chat_service, "stream", fake_stream)
    client.delete("/api/chat/messages", headers=auth_headers)

    body = _events(client, auth_headers, "học bổng?")
    assert 'data: {"delta": "Xin "}' in body and "event: done" in body

    messages = client.get("/api/chat/messages", headers=auth_headers).json()
    assert [(m["role"], m["content"]) for m in messages] == [("user", "học bổng?"), ("bot", "Xin chào")]


def test_chat_error_event(client, auth_headers, monkeypatch):
    async def broken_stream(query):
        yield "a"
        raise RuntimeError("boom")

    monkeypatch.setattr(chat_service, "stream", broken_stream)
    assert "event: error" in _events(client, auth_headers, "x")


def test_clear_messages(client, auth_headers):
    assert client.delete("/api/chat/messages", headers=auth_headers).status_code == 204
    assert client.get("/api/chat/messages", headers=auth_headers).json() == []
