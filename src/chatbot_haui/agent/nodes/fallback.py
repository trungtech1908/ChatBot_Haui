from chatbot_haui.agent.state import AgentState


def node_fallback(state: AgentState) -> AgentState:
    state["answer"] = (
        "Xin lỗi, hiện tại em chưa thể trả lời đầy đủ và chính xác câu hỏi này "
        "dựa trên quy chế và dữ liệu có sẵn. "
        "Bạn vui lòng hỏi lại cụ thể hơn hoặc liên hệ Phòng Đào tạo / Công tác sinh viên HaUI "
        "để được hỗ trợ trực tiếp."
    )
    state["quality_ok"] = True
    return state
