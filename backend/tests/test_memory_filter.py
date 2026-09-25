"""Bộ lọc memory (ARCHITECTURE 2.10): chỉ giữ cách giao tiếp, chủ đề, mục tiêu, câu hỏi dở dang."""
import pytest

from chatbot_haui.ai.memory import is_allowed, user_key


@pytest.mark.parametrize("text", [
    "Sinh viên muốn câu trả lời ngắn gọn, có trích dẫn điều khoản",
    "Sinh viên đang tìm hiểu học bổng khuyến khích học tập",
    "Sinh viên quan tâm khoản nợ học phí kỳ này",
    "Sinh viên muốn đạt học bổng loại Giỏi",
    "Sinh viên định học cải thiện môn Giải tích ở kỳ hè",
    "Sinh viên đang hỏi dở thủ tục xin miễn giảm học phí, chưa hỏi phần hồ sơ",
])
def test_allowed_categories_kept(text):
    assert is_allowed(text)


@pytest.mark.parametrize("text", [
    # con số học vụ, tài chính, định danh
    "Sinh viên có GPA 3.2",
    "Sinh viên còn nợ 9541800 đồng",
    "Sinh viên học khóa K19",
    "Email của sinh viên là a@gmail.com",
    # hoàn cảnh nhạy cảm — có dấu và không dấu
    "Sinh viên thuộc hộ nghèo",
    "Sinh vien thuoc ho can ngheo",
    "Sinh viên là người khuyết tật",
    "Sinh viên là người dân tộc Tày",
    "Sinh viên mồ côi cha",
    "Sinh viên đang điều trị bệnh",
    "Sinh viên có hoàn cảnh khó khăn",
    # kỷ luật, cảnh báo, thôi học
    "Sinh viên từng bị kỷ luật khiển trách",
    "Sinh viên lo bị cảnh báo học tập",
    "Sinh viên sợ bị buộc thôi học",
    # định danh
    "Sinh viên muốn đổi số điện thoại",
    "Sinh viên hỏi về địa chỉ thường trú",
    # thông tin về người khác
    "Sinh viên quan tâm đến điểm của sinh viên khác",
    "Sinh viên muốn xem học bổng của bạn cùng lớp",
    "Sinh vien hoi diem cua nguoi khac",
    "",
])
def test_forbidden_content_blocked(text):
    assert not is_allowed(text)


def test_user_key_is_stable_and_hides_student_id():
    key = user_key("2024619567")
    assert key == user_key("2024619567") != user_key("2024619568")
    assert "2024619567" not in key and len(key) == 32
