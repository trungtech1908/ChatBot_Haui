# Đánh giá chatbot

Script `backend/scripts/evaluate.py` chạy đúng graph của backend (`chatbot_haui/ai/graph.py`) trên bộ câu hỏi có đáp án mẫu, dùng LLM làm giám khảo so với đáp án mẫu, và tính thêm độ phủ văn bản của RAG.

Script chạy riêng trên máy, **không nằm trong Docker**, và **gọi API thật** (LLM, Qdrant, Cohere; trace lên Langfuse nếu bật). Mỗi câu tốn 5–8 lần gọi LLM cho luồng + 1 lần cho giám khảo: chạy thử với `--limit` trước, tránh cạn quota.

## Luồng

```
mỗi câu ──► graph đầy đủ (như lượt đầu của một hội thoại mới, đăng nhập bằng --student)
        ──► LLM giám khảo: so câu trả lời với đáp án mẫu → pass/fail
        ──► doc recall: văn bản nguồn của đáp án mẫu có nằm trong các chunk RAG truy hồi được không
        ──► ghi kết quả + in tổng hợp
```

## Yêu cầu

- Database đã khởi tạo ([database.md](database.md)): mỗi câu chạy trong phiên của một sinh viên mẫu
- Collection hybrid đã có trên Qdrant ([ingest.md](ingest.md))
- `.env` đã điền LLM, Qdrant, Cohere (Langfuse tùy chọn)

## Chạy

```bash
cd backend
uv sync --extra cpu
uv run --no-sync python scripts/evaluate.py ../haui_qa_dataset.json --limit 20 -o eval_results.json
```

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `questions` | | File câu hỏi |
| `-o`, `--output` | `eval_results.json` | File kết quả chi tiết |
| `--student` | `2024619567` | Mã sinh viên đăng nhập khi hỏi |
| `--limit`, `--offset` | tất cả, `0` | Chạy một đoạn của bộ câu hỏi |

File câu hỏi (định dạng của `haui_qa_dataset.json`; định dạng cũ `[{"Question", "Answer"}]` vẫn đọc được):

```json
[{"id": "haui-0001", "question": "...", "answer": "...", "source": ["TinhHocPhi.pdf"], "answerable": true}]
```

Output mẫu (số liệu minh họa, không phải kết quả đã chạy):

```
[1/20] pass  recall=1.0 học phí kỳ này của em bao nhiêu ạ
...
PASS: 15/20 (75.0%); lỗi: 0
  answerable: 13/16
  không trả lời được: 2/4
Doc recall TB (câu có chạy RAG): 82.5% trên 18 câu
```

Mỗi mục trong file kết quả có: câu trả lời, route, các bước đã chạy (`sql:ok`, `rag:ok`...), văn bản truy hồi được, doc recall, lý do fallback, và nhận xét của giám khảo. Với trace Langfuse, lọc theo tag `evaluate`.

## Lưu ý khi đọc kết quả

- `haui_qa_dataset.json` chủ yếu là câu hỏi quy chế chung. Câu có yếu tố cá nhân ("học phí kỳ này của em") sẽ được trả lời bằng dữ liệu của `--student`; giám khảo được dặn không trừ điểm phần số liệu cá nhân, nhưng vẫn có thể lệch với đáp án mẫu viết chung chung.
- Script mới đo chất lượng câu trả lời và RAG. Text2SQL (execution accuracy), Router, Planner và các câu tấn công cần bộ câu hỏi riêng; phần bảo mật đã có test tự động trong `backend/tests/` (`test_sql_guard.py`, `test_db_security.py`).
- Giám khảo dùng model chính (`LLM_PROVIDER`), có fallback như luồng chính.
