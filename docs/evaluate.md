# Đánh giá chất lượng RAG

Script `backend/scripts/evaluate.py` chạy đúng luồng chatbot backend đang dùng (`chatbot_haui/ai/graph.py`) trên một bộ câu hỏi có đáp án mẫu, rồi dùng LLM làm giám khảo so sánh đáp án RAG với đáp án mẫu và tính tỉ lệ pass.

Script này chạy riêng trên máy, **không nằm trong Docker**.

## Luồng xử lý

```
Mỗi câu hỏi ──► ai/graph.py (viết lại câu hỏi → phân loại → truy xuất Qdrant + rerank → trả lời)
            ──► LLM giám khảo: so đáp án RAG với đáp án mẫu
            ──► ghi kết quả + in tỉ lệ pass
```

## Yêu cầu

- Dữ liệu đã được nạp lên Qdrant (xem [ingest.md](ingest.md))
- [uv](https://docs.astral.sh/uv/)
- Không cần GPU

## Cấu hình

Dùng chung `.env` ở thư mục gốc repo với backend:

| Biến                              | Bắt buộc | Mô tả                                         |
|-----------------------------------|----------|-----------------------------------------------|
| `LLM_PROVIDER`                    | ✔        | `google` hoặc `groq`, dùng cho cả RAG và giám khảo |
| `GOOGLE_API_KEY` / `GROQ_API_KEY` | ✔        | Key theo provider đã chọn                     |
| `GOOGLE_MODEL` / `GROQ_MODEL`     |          | Đổi model nếu cần                             |
| `QDRANT_URL`, `QDRANT_API_KEY`    | ✔        | Qdrant Cloud                                  |
| `QDRANT_COLLECTION`               |          | Collection cần đánh giá                       |
| `COHERE_API_KEY`                  | ✔        | Rerank                                        |

## Chuẩn bị bộ câu hỏi

File JSON, mỗi phần tử gồm câu hỏi và đáp án mẫu:

```json
[
  {
    "Question": "Sinh viên cần tích lũy tối thiểu bao nhiêu tín chỉ để tốt nghiệp?",
    "Answer": "Tối thiểu 120 tín chỉ, chưa tính Giáo dục thể chất và Giáo dục quốc phòng - an ninh."
  }
]
```

Đáp án mẫu nên lấy đúng theo nội dung PDF trong `backend/assets/documents/`.

## Chạy

Từ thư mục `backend/`:

```bash
cd backend

# Cài môi trường (torch bản CPU cho embedding)
uv sync --extra cpu

# Đánh giá
uv run python scripts/evaluate.py questions.json -o eval_results.json
```

| Tham số          | Mô tả                                            |
|------------------|--------------------------------------------------|
| `questions.json` | Đường dẫn file câu hỏi                           |
| `-o`, `--output` | File kết quả, mặc định `eval_results.json` (đã gitignore) |

Các câu được chạy tuần tự. Output mẫu:

```
[1/50] pass
[2/50] fail
...
PASS: 41/50 (82.00%)
```

## Đọc kết quả

Mỗi phần tử trong file kết quả:

```json
{
  "question": "...",
  "category": ["QuyCheDaoTao"],
  "reference_answer": "...",
  "rag_answer": "...",
  "judge": {
    "factual_alignment": 4,
    "missing_information": "no",
    "extra_information": "yes",
    "contradiction": "no",
    "semantic_equivalence": "high",
    "final_verdict": "pass",
    "reason": "..."
  }
}
```

| Trường                 | Ý nghĩa                                           |
|------------------------|---------------------------------------------------|
| `category`             | Tài liệu bước phân loại chọn; `Không xác định` = không tra cứu |
| `factual_alignment`    | Mức khớp sự thật, 1–5                             |
| `missing_information`  | RAG thiếu ý so với đáp án mẫu                     |
| `extra_information`    | RAG thêm ý không có trong đáp án mẫu              |
| `contradiction`        | RAG mâu thuẫn với đáp án mẫu                      |
| `semantic_equivalence` | Mức tương đương về ý nghĩa                        |
| `final_verdict`        | `pass` / `fail`                                   |

Khi câu bị `fail`, xem `category` trước: phân loại sai tài liệu thì sửa mô tả trong `backend/src/chatbot_haui/ai/prompts/document_descriptions.json`, phân loại đúng mà vẫn sai thì vấn đề nằm ở truy xuất hoặc chunk.

## Lưu ý

- Mỗi câu hỏi gọi LLM 4 lần (viết lại câu hỏi, phân loại, trả lời, chấm) và 1 lần Cohere rerank; chú ý giới hạn rate limit của gói API, nhất là Groq free tier.
- Giám khảo dùng cùng LLM với RAG (theo `LLM_PROVIDER`), nên kết quả mang tính tương đối; so sánh giữa các lần chạy thì giữ nguyên provider và model.
