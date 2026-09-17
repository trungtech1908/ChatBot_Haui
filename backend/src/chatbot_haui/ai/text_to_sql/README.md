# Text-to-SQL (thử nghiệm)

Prototype hỏi đáp dữ liệu sinh viên bằng SQL, **chưa tích hợp vào API**.

- `intent_understanding.py`: hiểu ý định câu hỏi, xuất `intent_understanding_output.json`
- `step3.py`: lập kế hoạch truy vấn từ intent
- `describe_DB.json`: mô tả schema database

Chạy từ `backend/`: `uv run python -m chatbot_haui.ai.text_to_sql.intent_understanding`
