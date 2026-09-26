# Nạp tài liệu lên Qdrant

Script `backend/scripts/ingest.py` đọc PDF trong `backend/assets/documents/`, OCR từng trang, chia chunk rồi embedding và đẩy lên Qdrant Cloud.

Script này chạy riêng trên máy hoặc Google Colab, **không nằm trong Docker**. Chỉ cần chạy khi lần đầu dựng dữ liệu, hoặc khi thêm/sửa PDF.

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
| `source`   | Tên file PDF không đuôi, ví dụ `HocBong`     |
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
| `QDRANT_COLLECTION` |          | Collection văn bản chatbot dùng, mặc định `RAG_ChatBot_HAUI`; script **xóa rồi tạo lại** |
| `DOCUMENTS_DIR`     |          | Thư mục PDF, mặc định `assets/documents` (tính từ `backend/`) |
| `EMBEDDING_MODEL`   |          | Mặc định `BAAI/bge-m3`                          |

OCR tốn GPU và chạy lâu, nên chunk được lưu ra `backend/assets/chunks.json`. Lần sau chỉ cần dựng lại index từ file này (`--from-chunks`), không cần GPU.

## Chạy

Tất cả lệnh chạy từ thư mục `backend/`.

```bash
cd backend

# Cài môi trường: torch bản CUDA + thư viện OCR
uv sync --extra gpu --extra ingest

# OCR → chunk (lưu assets/chunks.json) → embedding + BM25 → Qdrant
uv run --no-sync python scripts/ingest.py
```

Trước khi OCR, script kiểm tra hết; sai chỗ nào dừng ngay ở đó kèm lý do: có PDF không, ghi được vào `assets/` không, Qdrant URL/key đúng và có quyền ghi không, có GPU và poppler không, tải được model không.

Tiến độ OCR được lưu sau **từng PDF** vào `assets/chunks.partial.json`, chỉ thay vào `assets/chunks.json` khi đã OCR đủ mọi PDF (nên lần chạy lỗi không ghi đè bản đầy đủ). Lỗi giữa chừng thì chạy lại đúng lệnh cũ: các PDF đã OCR được bỏ qua. Muốn OCR lại từ đầu thì thêm `--fresh`. Lỗi ở bước đẩy lên Qdrant thì chạy `--from-chunks`, không phải OCR lại.

Chỉ dựng lại index (đổi cách mã hóa, mất collection trên Qdrant...), không OCR, không cần GPU:

```bash
cd backend
uv sync --extra cpu
uv run --no-sync python scripts/ingest.py --from-chunks
```

Lần đầu chạy sẽ tải model Nanonets (~7GB) và bge-m3 (~2GB) về `~/.cache/huggingface`.

Output mẫu:

```
Xử lý ChinhSachSV.pdf
  OCR trang 1
  ...
  23 chunk
...
Đã lưu chunk ra .../backend/assets/chunks.json
Đã đẩy 166 chunk (dense + BM25) lên 'RAG_ChatBot_HAUI'
```

## Collection hybrid

Chatbot truy hồi hybrid: vector dense bge-m3 (ngữ nghĩa) và vector sparse BM25 (khớp chính xác cụm như "Điều 12", "học kỳ phụ"), hợp nhất bằng Reciprocal Rank Fusion ngay trên Qdrant, rồi rerank bằng Cohere lấy top 5.

Cấu trúc collection (định nghĩa ở `backend/src/chatbot_haui/ai/indexing.py`, dùng chung cho ingest và truy hồi):

| Payload / vector | Giá trị |
|---|---|
| `source` | Tên PDF không đuôi, ví dụ `HocBong` (có payload index) |
| `raw_text` | Nội dung chunk |
| `dense` | bge-m3, 1024 chiều, cosine |
| `bm25` | sparse: token = âm tiết + cặp âm tiết liền nhau (bigram), trọng số phần TF của BM25; IDF do Qdrant tính (`Modifier.IDF`) |

Chunk hiện chưa cắt theo Chương/Điều/Khoản, nên chatbot chỉ trích dẫn được ở mức tên văn bản và chưa lọc được theo hiệu lực, bậc, khóa.

## Chạy trên Google Colab

Không có GPU trên máy thì dùng `backend/scripts/ingest_colab.py`: file chạy độc lập, không cần clone repo hay cài uv, mọi cấu hình nằm ở đầu file.

1. Tạo notebook mới, vào **Runtime > Change runtime type** chọn **GPU** (T4 là đủ).
2. Đưa PDF lên Colab, chọn một trong hai cách:
   - Upload thẳng vào `/content/documents` (bảng Files bên trái), hoặc
   - Để PDF trên Google Drive, đặt `PDF_DIR = "/content/drive/MyDrive/<thư mục>"` và `MOUNT_DRIVE = True`.
3. Điền Qdrant: thêm `QDRANT_URL`, `QDRANT_API_KEY` vào **Colab Secrets** (biểu tượng chìa khóa bên trái, bật quyền cho notebook), hoặc điền thẳng vào đầu file (đừng chia sẻ notebook khi đã điền key).
4. Copy toàn bộ nội dung `ingest_colab.py` vào một cell và chạy.

Cấu hình ở đầu file:

| Biến                  | Mặc định                      | Mô tả                                              |
|-----------------------|-------------------------------|----------------------------------------------------|
| `PDF_DIR`             | `/content/drive/MyDrive/Colab Notebooks/documents`| Thư mục PDF                                        |
| `MOUNT_DRIVE`         | `True`                        | Mount Google Drive trước khi đọc PDF               |
| `QDRANT_COLLECTION`   | `RAG_ChatBot_HAUI`         | Phải trùng `QDRANT_COLLECTION` của backend; luôn xóa rồi nạp lại toàn bộ |
| `OCR_DPI`, `OCR_MAX_NEW_TOKENS` | `200`, `2048`       | Chất lượng ảnh và độ dài tối đa mỗi trang OCR      |
| `MAX_ITEMS_PER_CHUNK` | `6`                           | Luật chia chunk, giữ giống bản chạy trên máy       |
| `SAVE_CHUNKS_JSON`    | `/content/drive/MyDrive/Colab Notebooks/documents/chunks.json`| File lưu chunk, ghi sau **từng PDF**. Tải về chép vào `backend/assets/chunks.json` |
| `REUSE_CHUNKS`        | `True`                        | PDF đã có trong `SAVE_CHUNKS_JSON` thì bỏ qua OCR khi chạy lại |

Trước khi OCR, script kiểm tra hết rồi mới chạy; sai chỗ nào dừng ngay ở đó kèm lý do: thư mục PDF, file lưu chunk ghi được không, Qdrant URL kết nối được không, API key đúng và có quyền ghi không (thử tạo rồi xóa một collection tạm), có GPU không, tải được model OCR và embedding không. Lỗi ở bước đẩy lên Qdrant không làm mất kết quả OCR: sửa lỗi rồi chạy lại cell, các PDF đã OCR được bỏ qua.

Lần chạy đầu tải model Nanonets (~7GB) và bge-m3 (~2GB), mất vài phút. Nếu Colab báo lỗi thư viện ngay sau bước cài đặt, chọn **Runtime > Restart session** rồi chạy lại cell.

Luật chia chunk ở `ingest.py` và `ingest_colab.py` giống hệt nhau; bộ mã hóa BM25 trong `ingest_colab.py` là bản chép của `ai/tools/sparse.py` (test `test_colab_copy_matches_backend_encoder` báo nếu lệch). Sửa thì sửa cả hai nơi.

## Thêm hoặc sửa tài liệu

1. Chép PDF vào `backend/assets/documents/`. Tên file không dấu, không khoảng trắng, ví dụ `QuyCheThiCu.pdf`.
2. Thêm mô tả vào `backend/src/chatbot_haui/ai/prompts/document_descriptions.json`, **key trùng tên file PDF** (bỏ `.pdf`):
   ```json
   { "QuyCheThiCu": "Quy chế tổ chức thi: lịch thi, quy định phòng thi, xử lý vi phạm..." }
   ```
   Planner dựa vào mô tả này để chọn văn bản cần lọc khi tra cứu. Thêm tên hiển thị (có số quyết định) vào `TITLES` trong `backend/src/chatbot_haui/ai/documents.py` để câu trả lời trích dẫn đúng tên văn bản.
3. Chạy lại `scripts/ingest.py` (hoặc bản Colab). Script nạp lại **toàn bộ** PDF, không nạp riêng file mới.

Không cần build lại Docker: backend đọc thẳng từ Qdrant. Nếu có sửa `document_descriptions.json` hoặc `documents.py` thì build lại backend: `docker compose up -d --build backend`.

## Lỗi thường gặp

| Lỗi                                         | Cách xử lý                                              |
|---------------------------------------------|---------------------------------------------------------|
| `PDFInfoNotInstalledError`                  | Chưa cài `poppler-utils`                                |
| `CUDA out of memory`                        | Đóng ứng dụng khác dùng GPU, hoặc dùng GPU nhiều VRAM hơn |
| `Không có PDF trong assets/documents`       | Kiểm tra `DOCUMENTS_DIR` và vị trí chạy lệnh (`backend/`) |
| `Unauthorized` / `403` từ Qdrant            | Sai `QDRANT_URL` hoặc `QDRANT_API_KEY`                   |
