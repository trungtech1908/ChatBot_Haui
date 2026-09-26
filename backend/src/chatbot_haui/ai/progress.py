"""Chuyển sự kiện của graph (astream_events v2) thành tiến trình hiển thị cho sinh viên.

Mỗi bước hiển thị ứng với việc graph THẬT SỰ làm: nhãn lấy theo node đang chạy và công cụ có trong kế hoạch,
không có nhãn cố định kiểu "đang tra quy chế" khi kế hoạch chỉ tra dữ liệu. Nội dung viết cho sinh viên đọc,
không lộ SQL, tên bảng hay tên model.

Câu trả lời được stream từng token từ Generator/Direct. Validator chạy sau nên bản nháp có thể bị bác:
khi đó phát `reset` để client xóa phần đã hiện, rồi stream bản mới (hoặc câu trả lời dự phòng).
"""
from dataclasses import dataclass, field
from typing import Any

# Sự kiện executor tự phát cho từng bước kế hoạch (adispatch_custom_event)
STEP_START = "plan_step_start"
STEP_END = "plan_step_end"

STREAM_NODES = ("generator", "direct")  # node có token câu trả lời gửi cho sinh viên

TOOL_LABEL = {
    "sql": "Tra cứu dữ liệu học vụ của bạn",
    "rag": "Tìm trong văn bản quy chế",
    "compute": "Tính toán",
}
ROUTE_DETAIL = {
    "can_tra_cuu": "Cần tra cứu thông tin để trả lời",
    "da_co_trong_lich_su": "Câu này vừa được trả lời ở trên, dùng lại câu trả lời đó",
    "out_of_scope": "Câu hỏi nằm ngoài phạm vi hỗ trợ",
}
VERDICT_DETAIL = {
    "OK": ("done", "Câu trả lời khớp với dữ liệu và văn bản đã tra"),
    "KHANG_DINH_SAI": ("error", "Có chỗ chưa khớp với nguồn, đang viết lại"),
    "THIEU_BANG_CHUNG": ("error", "Còn thiếu thông tin, cần tra cứu thêm"),
    "KHONG_THE_TRA_LOI": ("error", "Không đủ căn cứ để trả lời chắc chắn"),
}


@dataclass
class Out:
    kind: str  # step | delta | reset | answer
    data: dict


def step(id: str, label: str, status: str, detail: str = "") -> Out:
    return Out("step", {"id": id, "label": label, "status": status, "detail": detail})


def _step_done_detail(result: dict) -> tuple[str, str]:
    """(status, detail) cho một bước kế hoạch đã chạy xong."""
    status, out = result.get("status"), result.get("output") or {}
    if status == "unsupported":
        return "error", "Hệ thống không có dữ liệu này"
    if status == "skipped":
        return "error", "Bỏ qua vì bước trước chưa có kết quả"
    if status != "ok":
        return "error", "Chưa tra được thông tin này"
    if result.get("tool") == "sql":
        n = len(out.get("rows") or [])
        return "done", f"Tìm thấy {n} kết quả" if n else "Không có dữ liệu phù hợp"
    if result.get("tool") == "rag":
        titles = list(dict.fromkeys(c["title"] for c in out.get("chunks", [])))
        return "done", ("Căn cứ: " + "; ".join(titles)) if titles else "Không tìm thấy đoạn văn bản phù hợp"
    return "done", "Đã tính xong"


@dataclass
class Progress:
    """Theo dõi một lượt hỏi; feed() nhận từng sự kiện graph, trả về các sự kiện gửi client."""
    plans: int = 0
    answers: int = 0
    checks: int = 0
    last_verdict: str = ""
    route: str = ""
    streamed: bool = False  # đã gửi token của lần sinh hiện tại
    open_steps: dict[str, tuple[str, str]] = field(default_factory=dict)  # id → (label, detail) đang chạy

    def _start(self, id: str, label: str, detail: str = "") -> Out:
        self.open_steps[id] = (label, detail)
        return step(id, label, "running", detail)

    def _end(self, id: str, status: str = "done", detail: str | None = None) -> list[Out]:
        if id not in self.open_steps:
            return []
        label, start_detail = self.open_steps.pop(id)
        return [step(id, label, status, start_detail if detail is None else detail)]

    def _reset(self) -> list[Out]:
        if not self.streamed:
            return []
        self.streamed = False
        return [Out("reset", {})]

    def feed(self, event: dict) -> list[Out]:
        kind, name = event["event"], event.get("name")
        node = (event.get("metadata") or {}).get("langgraph_node")
        data: dict[str, Any] = event.get("data") or {}
        is_node = name == node  # sự kiện của chính node, không phải runnable con bên trong

        if kind == "on_custom_event" and name == STEP_START:
            return [self._start(data["id"], TOOL_LABEL.get(data["tool"], "Tra cứu"), data.get("purpose", ""))]
        if kind == "on_custom_event" and name == STEP_END:
            status, detail = _step_done_detail(data["result"])
            return self._end(data["id"], status, detail)

        if kind == "on_chat_model_start" and node in STREAM_NODES:
            return self._reset()  # model dự phòng chạy lại từ đầu sau khi model chính lỗi giữa chừng
        if kind == "on_chat_model_stream" and node in STREAM_NODES:
            chunk = data.get("chunk")
            text = getattr(chunk, "text", "") or ""
            if not isinstance(text, str) or not text:
                return []
            self.streamed = True
            return [Out("delta", {"text": text})]

        if not is_node:
            return []
        output = data.get("output") or {}

        if kind == "on_chain_start":
            if node == "rewriter":
                return [self._start("understand", "Đọc hiểu câu hỏi")]
            if node == "memory_read":
                return [self._start("memory", "Xem lại những điều bạn từng chia sẻ")]
            if node == "planner":
                self.plans += 1
                label = "Xác định cần tra cứu những gì" if self.plans == 1 else "Tra cứu bổ sung phần còn thiếu"
                return [self._start(f"plan-{self.plans}", label)]
            if node == "generator":
                self.answers += 1
                label = "Viết lại câu trả lời cho chính xác" if self.last_verdict == "KHANG_DINH_SAI" else "Soạn câu trả lời"
                return self._reset() + [self._start(f"answer-{self.answers}", label)]
            if node == "direct" and self.route != "da_co_trong_lich_su":  # dùng lại câu cũ thì không soạn gì
                return [self._start("answer-1", "Soạn câu trả lời")]
            if node == "validator":
                self.checks += 1
                return [self._start(f"check-{self.checks}", "Đối chiếu câu trả lời với nguồn")]
            if node == "fallback":
                return self._reset()
            return []

        if kind == "on_chain_end":
            if node == "router":
                self.route = output.get("route", "")
                return self._end("understand", detail=ROUTE_DETAIL.get(output.get("route"), ""))
            if node == "memory_read":
                n = len(output.get("memories") or [])
                return self._end("memory", detail=f"Nhớ lại {n} điều liên quan" if n else "Chưa có điều gì liên quan")
            if node == "planner":
                n = len((output.get("plan") or {}).get("new_steps") or [])
                return self._end(f"plan-{self.plans}", detail=f"{n} việc cần làm" if n else "Không tìm được cách tra cứu phù hợp")
            if node in ("generator", "direct"):
                return self._end(f"answer-{max(self.answers, 1)}")
            if node == "validator":
                self.last_verdict = (output.get("verdict") or {}).get("verdict", "")
                status, detail = VERDICT_DETAIL.get(self.last_verdict, ("error", ""))
                out = self._end(f"check-{self.checks}", status, detail)
                return out + (self._reset() if self.last_verdict != "OK" else [])
        return []

