"""Tiến trình hiển thị cho sinh viên (ai/progress.py) chạy trên graph thật với LLM giả.

Kiểm chứng: bước hiển thị khớp với việc graph thật sự làm (không hiện "tra quy chế" khi kế hoạch chỉ tra dữ liệu),
token câu trả lời được stream, bản nháp bị bác / model chạy lại thì client được báo xóa phần đã hiện.
"""
from collections.abc import AsyncIterator

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.output_parsers import StrOutputParser
from langchain_core.outputs import ChatGenerationChunk
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from test_graph_flow import OK, Script, _inputs, _plan

from chatbot_haui.ai import graph as graph_module
from chatbot_haui.ai import progress
from chatbot_haui.ai.nodes import answering
from chatbot_haui.ai.nodes.answering import Verdict
from chatbot_haui.ai.nodes.planning import Step
from chatbot_haui.ai.prompts import answer as answer_prompts

SQL = Step(id="s1", tool="sql", query="các môn đang học kỳ này", purpose="Lấy danh sách môn bạn đang học")
RAG = Step(id="s2", tool="rag", query="điều kiện học bổng", purpose="Tìm điều kiện xét học bổng")


def _stream_generator(monkeypatch, *drafts: str, model=None):
    """Generator dùng chat model giả stream từng từ; mỗi lần gọi trả bản nháp kế tiếp."""
    fake = model or GenericFakeChatModel(messages=iter(AIMessage(content=d) for d in drafts))
    chain = ChatPromptTemplate.from_messages([("human", "{question}")]) | fake | StrOutputParser()
    monkeypatch.setattr(answering, "_generator", lambda: chain)


async def _run(query="tôi đang học những môn gì", thread="t1"):
    g = graph_module.build_graph(MemorySaver())
    p, outs, answer = progress.Progress(), [], None
    async for event in g.astream_events(_inputs(query), {"configurable": {"thread_id": thread}}, version="v2"):
        outs += p.feed(event)
        if event["event"] == "on_chain_end" and not event.get("parent_ids"):
            answer = event["data"]["output"]["answer"]
    return outs, answer


def _final_steps(outs):
    """id → lần cập nhật cuối của bước, theo thứ tự xuất hiện."""
    steps = {}
    for o in outs:
        if o.kind == "step":
            steps[o.data["id"]] = o.data
    return steps


def _shown_text(outs):
    """Phần câu trả lời client đang hiện sau khi áp mọi delta / reset."""
    text = ""
    for o in outs:
        if o.kind == "delta":
            text += o.data["text"]
        elif o.kind == "reset":
            text = ""
    return text


async def test_data_only_plan_shows_data_lookup_not_regulations(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(SQL)], verdicts=[OK])
    _stream_generator(monkeypatch, "Bạn đang học Lập trình Web và Trí tuệ nhân tạo.")
    outs, answer = await _run()

    steps = _final_steps(outs)
    assert list(steps) == ["understand", "memory", "plan-1", "s1", "answer-1", "check-1"]
    assert steps["s1"]["label"] == progress.TOOL_LABEL["sql"] and steps["s1"]["detail"] == "Tìm thấy 1 kết quả"
    labels = " ".join(f"{o.data['label']} {o.data['detail']}" for o in outs if o.kind == "step").lower()
    assert "quy chế" not in labels and "rag" not in s.calls
    assert all(st["status"] == "done" for st in steps.values())


async def test_every_started_step_is_reported_running_before_done(monkeypatch):
    Script(monkeypatch, plans=[_plan(SQL, RAG)], verdicts=[OK])
    _stream_generator(monkeypatch, "Trả lời.")
    outs, _ = await _run()
    seen: dict[str, list[str]] = {}
    for o in outs:
        if o.kind == "step":
            seen.setdefault(o.data["id"], []).append(o.data["status"])
    assert all(v[0] == "running" and v[-1] in ("done", "error") and len(v) == 2 for v in seen.values())


async def test_mixed_plan_shows_each_tool_and_regulation_sources(monkeypatch):
    Script(monkeypatch, plans=[_plan(SQL, RAG)], verdicts=[OK])
    _stream_generator(monkeypatch, "Bạn đủ điều kiện.")
    steps = _final_steps((await _run())[0])
    assert steps["s1"]["label"] == progress.TOOL_LABEL["sql"]
    assert steps["s2"]["label"] == progress.TOOL_LABEL["rag"]
    assert steps["s2"]["detail"] == "Căn cứ: Quy định xét học bổng"
    assert steps["plan-1"]["detail"] == "2 việc cần làm"


async def test_answer_tokens_stream_before_validation_and_match_final_answer(monkeypatch):
    Script(monkeypatch, plans=[_plan(SQL)], verdicts=[OK])
    draft = "Bạn đang học Lập trình Web, Trí tuệ nhân tạo và Công nghệ phần mềm."
    _stream_generator(monkeypatch, draft)
    outs, answer = await _run()

    kinds = [o.kind if o.kind != "step" else f"step:{o.data['id']}:{o.data['status']}" for o in outs]
    deltas = [i for i, k in enumerate(kinds) if k == "delta"]
    assert len(deltas) > 1  # nhiều token, không phải một khối
    assert deltas[-1] < kinds.index("step:check-1:running")  # hiện chữ trước khi kiểm định xong
    assert _shown_text(outs) == answer == draft


async def test_rejected_draft_is_cleared_then_rewritten(monkeypatch):
    sai = Verdict(verdict="KHANG_DINH_SAI", loi=["sai tên môn"])
    Script(monkeypatch, plans=[_plan(SQL)], verdicts=[sai, OK])
    _stream_generator(monkeypatch, "Bản nháp sai tên môn.", "Bản đã sửa đúng.")
    outs, answer = await _run()

    kinds = [o.kind for o in outs]
    first_reset = kinds.index("reset")
    assert "delta" in kinds[:first_reset] and "delta" in kinds[first_reset:]
    steps = _final_steps(outs)
    assert steps["check-1"]["status"] == "error" and steps["check-2"]["status"] == "done"
    assert steps["answer-2"]["label"] == "Viết lại câu trả lời cho chính xác"
    assert _shown_text(outs) == answer == "Bản đã sửa đúng."


async def test_fallback_answer_replaces_streamed_draft(monkeypatch):
    thieu = Verdict(verdict="THIEU_BANG_CHUNG", thieu=["hạn nộp"])
    Script(monkeypatch, plans=[_plan(SQL), _plan(Step(id="s2", tool="rag", query="hạn nộp", purpose="Tìm hạn nộp"))],
           verdicts=[thieu, thieu])
    _stream_generator(monkeypatch, "Nháp một.", "Nháp hai.")
    outs, answer = await _run("em nợ bao nhiêu, hạn khi nào")

    assert answer == answer_prompts.FALLBACK
    assert _shown_text(outs) == ""  # nháp đã bị xóa; client hiện `answer` cuối
    steps = _final_steps(outs)
    assert steps["plan-2"]["label"] == "Tra cứu bổ sung phần còn thiếu"
    assert steps["check-2"]["status"] == "error"


async def test_failed_lookup_step_is_reported_as_error(monkeypatch):
    Script(monkeypatch, plans=[_plan(SQL, RAG)], verdicts=[OK], rag="error")
    _stream_generator(monkeypatch, "Trả lời một phần.")
    steps = _final_steps((await _run())[0])
    assert (steps["s1"]["status"], steps["s2"]["status"]) == ("done", "error")
    assert steps["s2"]["detail"] == "Chưa tra được thông tin này"


class _FailsMidStream(GenericFakeChatModel):
    """Model chính stream được một phần rồi lỗi (VD quá tải) — model dự phòng phải chạy lại từ đầu."""

    async def _astream(self, messages, stop=None, run_manager=None, **kwargs) -> AsyncIterator[ChatGenerationChunk]:
        chunk = ChatGenerationChunk(message=AIMessageChunk(content="Nửa câu "))
        if run_manager:
            await run_manager.on_llm_new_token("Nửa câu ", chunk=chunk)
        yield chunk
        raise RuntimeError("503 quá tải")


async def test_model_fallback_mid_stream_clears_partial_text(monkeypatch):
    Script(monkeypatch, plans=[_plan(SQL)], verdicts=[OK])
    primary = _FailsMidStream(messages=iter([]))
    backup = GenericFakeChatModel(messages=iter([AIMessage(content="Câu trả lời đầy đủ.")]))
    _stream_generator(monkeypatch, model=primary.with_fallbacks([backup]))
    outs, answer = await _run()
    kinds = [o.kind for o in outs]
    assert kinds.index("delta") < kinds.index("reset")
    assert _shown_text(outs) == answer == "Câu trả lời đầy đủ."


async def test_chitchat_has_no_lookup_steps(monkeypatch):
    Script(monkeypatch, route="chitchat")
    steps = _final_steps((await _run("chào bạn"))[0])
    assert list(steps) == ["understand", "answer-1"]


def test_unknown_route_or_events_emit_nothing():
    p = progress.Progress()
    assert p.feed({"event": "on_chain_start", "name": "RunnableSequence", "metadata": {"langgraph_node": "planner"}}) == []
    assert p.feed({"event": "on_chain_end", "name": "router", "metadata": {"langgraph_node": "router"},
                   "data": {"output": {"route": "can_tra_cuu"}}}) == []  # chưa mở bước thì không đóng
