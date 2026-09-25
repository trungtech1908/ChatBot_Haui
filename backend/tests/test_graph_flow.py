"""Luồng graph (ARCHITECTURE mục 3) với LLM và tool giả; wiring, state, executor, aggregator,
vòng lặp replan/regen, fallback và bộ nhớ phiên là code thật."""
from datetime import datetime, timedelta

import pytest
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import MemorySaver

from chatbot_haui.ai import graph as graph_module
from chatbot_haui.ai.nodes import answering, conversation, executor, planning
from chatbot_haui.ai.nodes.answering import Verdict
from chatbot_haui.ai.nodes.conversation import RouteDecision
from chatbot_haui.ai.nodes.planning import Plan, Step
from chatbot_haui.ai.prompts import answer as answer_prompts


class Script:
    """Kịch bản trả lời cho từng chain giả + ghi lại số lần gọi."""

    def __init__(self, monkeypatch, *, route="can_tra_cuu", reuse=None, plans=(), verdicts=(), sql=None, rag=None):
        self.calls: dict[str, int] = {}
        self.plans, self.verdicts = list(plans), list(verdicts)
        self.inputs: dict[str, list] = {}

        def chain(name, fn):
            async def run(inp):
                self.calls[name] = self.calls.get(name, 0) + 1
                self.inputs.setdefault(name, []).append(inp)
                return fn(inp)
            return lambda: RunnableLambda(run)

        monkeypatch.setattr(conversation, "_rewriter", chain("rewriter", lambda i: i["query"] + " (viết lại)"))
        monkeypatch.setattr(conversation, "_router", chain("router", lambda i: RouteDecision(route=route, reuse_turn=reuse)))
        monkeypatch.setattr(conversation, "_direct", chain("direct", lambda i: "Chào bạn!"))
        monkeypatch.setattr(conversation, "_summarizer", chain("summary", lambda i: f"tóm tắt[{i['user']}]"))
        monkeypatch.setattr(planning, "_planner", chain("planner", lambda i: self.plans.pop(0)))
        monkeypatch.setattr(answering, "_generator", chain("generator", lambda i: f"nháp {self.calls['generator']}"))
        monkeypatch.setattr(answering, "_validator", chain("validator", lambda i: self.verdicts.pop(0)))

        async def recall(key, query):
            return ["Sinh viên muốn trả lời ngắn"]

        async def run_sql(question, ma_sv):
            self.calls["sql"] = self.calls.get("sql", 0) + 1
            self.inputs.setdefault("sql", []).append(question)
            return dict(sql or {"sql": "SELECT", "views": ["v_diem"], "columns": ["mon"], "rows": [{"mon": "Giải tích"}],
                               "row_count": 1, "empty": False, "gia_dinh": ""})

        async def run_rag(query, sources):
            self.calls["rag"] = self.calls.get("rag", 0) + 1
            self.inputs.setdefault("rag", []).append(query)
            if rag == "error":
                raise RuntimeError("Qdrant lỗi")
            return {"queries": [query], "sufficient": True,
                    "chunks": [{"source": "HocBong", "title": "Quy định xét học bổng", "text": "Điều 7 ...", "score": 0.9}]}

        monkeypatch.setattr(planning.memory, "recall", recall)
        monkeypatch.setattr(executor, "run_sql", run_sql)
        monkeypatch.setattr(executor, "run_rag", run_rag)


def _inputs(query, profile=None):
    return graph_module.turn_input(query, "2024619567", "key", profile or {"nganh": "Công nghệ thông tin"})


async def _ask(g, query, thread="t1"):
    return await g.ainvoke(_inputs(query), {"configurable": {"thread_id": thread}})


def _plan(*steps, focus="ý chính", khong_ho_tro=""):
    return Plan(steps=list(steps), answer_focus=focus, khong_ho_tro=khong_ho_tro)


OK = Verdict(verdict="OK")


async def test_chitchat_goes_direct_without_planning(monkeypatch):
    s = Script(monkeypatch, route="chitchat")
    state = await _ask(graph_module.build_graph(MemorySaver()), "chào bạn")
    assert state["answer"] == "Chào bạn!"
    assert "planner" not in s.calls and "rewriter" not in s.calls  # câu đầu tiên: không cần viết lại


async def test_parallel_sql_and_rag_then_validated_answer(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(
        Step(id="s1", tool="sql", query="điều kiện HB kỳ gần nhất", purpose="dữ liệu"),
        Step(id="s2", tool="rag", query="điều kiện học bổng KKHT", van_ban=["HocBong", "KhongCo"], purpose="căn cứ"),
    )], verdicts=[OK])
    state = await _ask(graph_module.build_graph(MemorySaver()), "em có đủ điều kiện học bổng không")
    assert state["answer"] == "nháp 1"
    assert {e["source"] for e in state["evidence"]} == {
        "dữ liệu của sinh viên (chatbot.v_diem)", "Quy định xét học bổng", answering.DATA_SOURCE}
    assert state["plan"]["steps"][1]["van_ban"] == ["HocBong"]  # mã văn bản không có thật bị bỏ
    gen_input = s.inputs["generator"][0]
    assert "Sinh viên muốn trả lời ngắn" in gen_input["memories"] and "2024619567" not in str(gen_input)


async def test_sequential_step_receives_previous_output(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(
        Step(id="s1", tool="sql", query="môn em trượt", purpose="môn F"),
        Step(id="s2", tool="rag", query="học lại học phần {s1.mon}", depends_on=["s1"], purpose="quy định"),
    )], verdicts=[OK])
    await _ask(graph_module.build_graph(MemorySaver()), "môn em trượt có được học lại hè không")
    assert s.inputs["rag"] == ["học lại học phần Giải tích"]


async def test_compute_binds_values_from_sql(monkeypatch):
    Script(monkeypatch, plans=[_plan(
        Step(id="s1", tool="sql", query="đơn giá và hệ số", purpose="số liệu"),
        Step(id="s2", tool="compute", expr="so_tc * he_so * don_gia", bien={"so_tc": "18", "he_so": "s1.he_so",
             "don_gia": "s1.don_gia"}, depends_on=["s1"], purpose="học phí dự kiến"),
    )], verdicts=[OK], sql={"sql": "SELECT", "views": ["v_don_gia"], "columns": ["don_gia", "he_so"],
                            "rows": [{"don_gia": 700000, "he_so": 1.0}], "row_count": 1, "empty": False})
    state = await _ask(graph_module.build_graph(MemorySaver()), "đăng ký 18 tín chỉ thì học phí bao nhiêu")
    assert state["results"]["s2"]["output"]["ket_qua"] == 12600000


async def test_other_person_question_falls_back_without_generation(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(khong_ho_tro="nguoi_khac")])
    state = await _ask(graph_module.build_graph(MemorySaver()), "điểm của bạn Nguyễn Văn A thế nào")
    assert state["answer"] == answer_prompts.FALLBACK_OTHER_PERSON
    assert "generator" not in s.calls and "sql" not in s.calls


async def test_sql_unsupported_other_person_also_falls_back(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="sql", query="GPA trung bình lớp", purpose="x"))],
               sql={"unsupported": "nguoi_khac", "gia_dinh": ""})
    state = await _ask(graph_module.build_graph(MemorySaver()), "GPA trung bình lớp em")
    assert state["answer"] == answer_prompts.FALLBACK_OTHER_PERSON and "generator" not in s.calls


async def test_wrong_claim_regenerates_once(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="sql", query="q", purpose="p"))],
               verdicts=[Verdict(verdict="KHANG_DINH_SAI", loi=["GPA 3.8 không có trong bằng chứng"]), OK])
    state = await _ask(graph_module.build_graph(MemorySaver()), "GPA của em")
    assert state["answer"] == "nháp 2" and s.calls["generator"] == 2
    assert "GPA 3.8 không có trong bằng chứng" in s.inputs["generator"][1]["fix"]


async def test_wrong_claim_twice_goes_to_fallback(monkeypatch):
    bad = Verdict(verdict="KHANG_DINH_SAI", loi=["sai"])
    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="sql", query="q", purpose="p"))], verdicts=[bad, bad])
    state = await _ask(graph_module.build_graph(MemorySaver()), "GPA của em")
    assert state["answer"] == answer_prompts.FALLBACK and s.calls["generator"] == 2


async def test_missing_evidence_replans_once_keeping_old_results(monkeypatch):
    thieu = Verdict(verdict="THIEU_BANG_CHUNG", thieu=["chưa nói hạn nộp"])
    s = Script(monkeypatch, plans=[
        _plan(Step(id="s1", tool="sql", query="công nợ", purpose="số nợ")),
        _plan(Step(id="s2", tool="rag", query="hạn nộp học phí", purpose="hạn nộp")),
    ], verdicts=[thieu, thieu])
    state = await _ask(graph_module.build_graph(MemorySaver()), "em nợ bao nhiêu, hạn khi nào")
    assert s.calls["planner"] == 2 and s.calls["sql"] == 1 and s.calls["rag"] == 1  # s1 không chạy lại
    assert state["answer"] == answer_prompts.FALLBACK  # vẫn thiếu sau 1 lần lập lại → fallback


async def test_failed_dependency_is_skipped_and_reported(monkeypatch):
    Script(monkeypatch, rag="error", plans=[_plan(
        Step(id="s1", tool="rag", query="quy định", purpose="căn cứ"),
        Step(id="s2", tool="sql", query="dùng {s1}", depends_on=["s1"], purpose="phụ thuộc"),
        Step(id="s3", tool="sql", query="độc lập", purpose="độc lập"),
    )], verdicts=[OK])
    state = await _ask(graph_module.build_graph(MemorySaver()), "câu hỏi")
    r = state["results"]
    assert (r["s1"]["status"], r["s2"]["status"], r["s3"]["status"]) == ("error", "skipped", "ok")
    assert state["missing"] == ["căn cứ", "phụ thuộc"]


async def test_session_history_rewrite_and_trim(monkeypatch):
    s = Script(monkeypatch, route="chitchat")
    g = graph_module.build_graph(MemorySaver())
    for i in range(8):
        state = await _ask(g, f"câu {i}")
    assert len(state["history"]) == conversation.MAX_TURNS
    assert state["history"][0]["user"] == "câu 2" and state["summary"] == "tóm tắt[câu 1]"
    assert s.calls["rewriter"] == 7  # từ câu thứ hai trở đi
    assert state["query_rewritten"] == "câu 7 (viết lại)"


async def test_repeat_question_reuses_answer_only_within_session(monkeypatch):
    Script(monkeypatch, route="chitchat")
    g = graph_module.build_graph(MemorySaver())
    await _ask(g, "câu đầu")

    s = Script(monkeypatch, route="da_co_trong_lich_su", reuse=1, plans=[_plan(khong_ho_tro="ngoai_pham_vi")])
    state = await _ask(g, "nhắc lại giúp mình")
    assert state["answer"] == "Chào bạn!" and "planner" not in s.calls

    # Lượt cũ đã quá SESSION_GAP → khác phiên → không được dùng lại, phải tra cứu
    config = {"configurable": {"thread_id": "t1"}}
    snapshot = await g.aget_state(config)
    old = [{**t, "at": (datetime.now() - timedelta(hours=2)).isoformat()} for t in snapshot.values["history"]]
    await g.aupdate_state(config, {"history": old})
    s = Script(monkeypatch, route="da_co_trong_lich_su", reuse=1, plans=[_plan(khong_ho_tro="ngoai_pham_vi")])
    state = await _ask(g, "nhắc lại giúp mình")
    assert s.calls.get("planner") == 1 and state["answer"] == answer_prompts.FALLBACK


@pytest.mark.parametrize("verdict, replan, regen, expected", [
    ("OK", 0, 0, "finalize"),
    ("THIEU_BANG_CHUNG", 0, 0, "planner"),
    ("THIEU_BANG_CHUNG", 1, 0, "fallback"),
    ("KHANG_DINH_SAI", 0, 0, "generator"),
    ("KHANG_DINH_SAI", 0, 1, "fallback"),
    ("KHONG_THE_TRA_LOI", 0, 0, "fallback"),
])
def test_validator_routing(verdict, replan, regen, expected):
    state = {"verdict": {"verdict": verdict}, "replan_count": replan, "regen_count": regen}
    assert graph_module.after_validator(state) == expected


async def test_data_timestamp_is_evidence_only_when_personal_data_used(monkeypatch):
    # Generator phải nêu ngày dữ liệu và Validator phải thấy ngày đó trong bằng chứng (nếu không sẽ bác là bịa)
    monkeypatch.setattr(answering.settings, "data_as_of", "31/08/2026")
    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="sql", query="công nợ", purpose="nợ"))], verdicts=[OK])
    await _ask(graph_module.build_graph(MemorySaver()), "em nợ bao nhiêu")
    assert "cập nhật đến ngày 31/08/2026" in s.inputs["validator"][0]["evidence"]
    assert "cập nhật đến ngày 31/08/2026" in s.inputs["generator"][0]["evidence"]

    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="rag", query="quy định", purpose="quy định"))], verdicts=[OK])
    await _ask(graph_module.build_graph(MemorySaver()), "học kỳ phụ là gì", thread="t2")
    assert "cập nhật đến ngày" not in s.inputs["validator"][0]["evidence"]


async def test_downstream_sees_original_question_when_rewriter_changes_scope(monkeypatch):
    # Rewriter (model nhỏ) có thể thu hẹp phạm vi; Planner/Generator/Validator phải thấy cả câu gốc
    s = Script(monkeypatch, route="chitchat")
    g = graph_module.build_graph(MemorySaver())
    await _ask(g, "chào bạn")
    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="sql", query="công nợ", purpose="nợ"))], verdicts=[OK])
    await _ask(g, "em còn nợ bao nhiêu")
    for node in ("planner", "generator", "validator"):
        q = s.inputs[node][0]["question"]
        assert "Câu hỏi gốc: em còn nợ bao nhiêu" in q and "(viết lại)" in q, node


async def test_question_shown_once_when_not_rewritten(monkeypatch):
    s = Script(monkeypatch, plans=[_plan(Step(id="s1", tool="sql", query="q", purpose="p"))], verdicts=[OK])
    await _ask(graph_module.build_graph(MemorySaver()), "GPA của em")
    assert s.inputs["planner"][0]["question"] == "Câu hỏi gốc: GPA của em"
