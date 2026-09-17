# Nạp tài liệu lên Qdrant

Script `backend/scripts/ingest.py` đọc PDF trong `backend/assets/documents/`, OCR từng trang, chia chunk rồi embedding và đẩy lên Qdrant Cloud.

Script này chạy riêng trên máy, **không nằm trong Docker**. Chỉ cần chạy khi lần đầu dựng dữ liệu, hoặc khi thêm/sửa PDF.

## Luồng xử lý

```
PDF ──► ảnh từng trang (pdf2image, 200 dpi)
    ──► OCR ra markdown (Nanonets-OCR2-3B, bỏ tag số trang/watermark)
    ──► chia chunk theo cấu trúc tiêu đề/mục (tối đa 6 mục/chunk)
    ──► embedding bge-m3 (vector 1024 chiều)
    ──► Qdrant: xóa collection cũ, tạo lại, upsert
```

Mỗi chunk lưu trên Qdrant có payload:

| Trường     | Giá trị                                      |
|------------|----------------------------------------------|
| `source`   | `<tên file PDF>.json`, ví dụ `HocBong.json`  |
| `raw_text` | Nội dung chunk                               |

## Yêu cầu

- GPU NVIDIA có driver CUDA (model OCR 3B chạy fp16, nên có từ ~8GB VRAM)
- `poppler-utils` để chuyển PDF sang ảnh:
  ```bash
  sudo apt install poppler-utils
  ```
- [uv](https://docs.astral.sh/uv/)

## Cấu hình

Trong `.env` ở thư mục gốc repo:

| Biến                | Bắt buộc | Mô tả                                           |
|---------------------|----------|-------------------------------------------------|
| `QDRANT_URL`        | ✔        | URL cluster Qdrant Cloud                        |
| `QDRANT_API_KEY`    | ✔        | API key Qdrant                                  |
| `QDRANT_COLLECTION` |          | Tên collection, mặc định `RAG_ChatBot_HAUI`     |
| `DOCUMENTS_DIR`     |          | Thư mục PDF, mặc định `assets/documents` (tính từ `backend/`) |
| `EMBEDDING_MODEL`   |          | Mặc định `BAAI/bge-m3`                          |

`QDRANT_COLLECTION` phải trùng với collection backend đang dùng.

## Chạy

Tất cả lệnh chạy từ thư mục `backend/`.

```bash
cd backend

# Cài môi trường: torch bản CUDA + thư viện OCR
uv sync --extra gpu --extra ingest

# Nạp tài liệu
uv run python scripts/ingest.py
```

Lần đầu chạy sẽ tải model Nanonets (~7GB) và bge-m3 (~2GB) về `~/.cache/huggingface`.

Output mẫu:

```
Xử lý ChinhSachSV.pdf
  OCR trang 1
  ...
  23 chunk
...
Đã đẩy 172 chunk lên 'RAG_ChatBot_HAUI'
```

## Thêm hoặc sửa tài liệu

1. Chép PDF vào `backend/assets/documents/`. Tên file không dấu, không khoảng trắng, ví dụ `QuyCheThiCu.pdf`.
2. Thêm mô tả vào `backend/src/chatbot_haui/ai/prompts/document_descriptions.json`, **key trùng tên file PDF** (bỏ `.pdf`):
   ```json
   { "QuyCheThiCu": "Quy chế tổ chức thi: lịch thi, quy định phòng thi, xử lý vi phạm..." }
   ```
   Bước phân loại câu hỏi dựa vào mô tả này để chọn tài liệu. Thiếu mô tả thì chatbot không bao giờ tìm tới tài liệu đó.
3. Chạy lại `uv run python scripts/ingest.py`. Script nạp lại **toàn bộ** PDF, không nạp riêng file mới.

Không cần build lại Docker: backend đọc thẳng từ Qdrant. Nếu có sửa `document_descriptions.json` thì build lại backend: `docker compose up -d --build backend`.

## Lỗi thường gặp

| Lỗi                                         | Cách xử lý                                              |
|---------------------------------------------|---------------------------------------------------------|
| `PDFInfoNotInstalledError`                  | Chưa cài `poppler-utils`                                |
| `CUDA out of memory`                        | Đóng ứng dụng khác dùng GPU, hoặc dùng GPU nhiều VRAM hơn |
| `Không có PDF trong assets/documents`       | Kiểm tra `DOCUMENTS_DIR` và vị trí chạy lệnh (`backend/`) |
| `Unauthorized` / `403` từ Qdrant            | Sai `QDRANT_URL` hoặc `QDRANT_API_KEY`                   |
