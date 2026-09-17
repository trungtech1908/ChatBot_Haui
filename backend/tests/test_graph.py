import sys
import types

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage


@pytest.fixture
def graph_module(monkeypatch):
    """Graph thật với LLM giả; thay node retrieve để không cần Qdrant/bge-m3."""
    import chatbot_haui.ai.llm as llm
    from chatbot_haui.ai import graph

    responses = iter([
        AIMessage(content="học bổng khuyến khích học tập"),  # query_transform
        AIMessage(content="HocBong.json, QuyCheDaoTao"),       # classify (LLM lỡ thêm đuôi .json)
        AIMessage(content="Bạn cần GPA từ 3.2"),               # answer
    ])
    fake_llm = GenericFakeChatModel(messages=responses)
    monkeypatch.setattr(llm, "get_llm", lambda: fake_llm)

    fake_retrieve = types.ModuleType("chatbot_haui.ai.nodes.retrieve")
    def retrieve(state):
        # Tên tài liệu đã được chuẩn hóa về đúng source trên Qdrant
        assert state["category"] == ["HocBong", "QuyCheDaoTao"]
        return {"retriever": ["Điều 5: GPA >= 3.2"]}

    fake_retrieve.retrieve = retrieve
    monkeypatch.setitem(sys.modules, "chatbot_haui.ai.nodes.retrieve", fake_retrieve)
    for name in ["chatbot_haui.ai.nodes", "chatbot_haui.ai.nodes.query_transform", "chatbot_haui.ai.nodes.classify",
                 "chatbot_haui.ai.nodes.answer"]:
        monkeypatch.delitem(sys.modules, name, raising=False)

    graph.get_graph.cache_clear()
    yield graph
    graph.get_graph.cache_clear()


async def test_stream_only_yields_answer_tokens(graph_module):
    tokens = [t async for t in graph_module.stream("em có được học bổng không")]
    assert "".join(tokens) == "Bạn cần GPA từ 3.2"


def test_route():
    from chatbot_haui.ai.graph import route
    from chatbot_haui.ai.prompts.classify import UNKNOWN

    assert route({"category": [UNKNOWN]}) == "answer_general"
    assert route({"category": []}) == "answer_general"
    assert route({"category": ["HocBong"]}) == "retrieve"
