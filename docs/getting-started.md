# Chạy dự án từ đầu

Hướng dẫn dựng toàn bộ hệ thống trên một máy mới, từ lúc clone code tới lúc đăng nhập và hỏi chatbot.

Tổng quan các bước:

| Bước | Việc cần làm                             | Chạy ở đâu               | Làm mấy lần                  |
|------|------------------------------------------|--------------------------|------------------------------|
| 1    | Cài công cụ, clone code                  | Máy                      | 1 lần                        |
| 2    | Lấy API key, tạo file `.env`             | Máy                      | 1 lần                        |
| 3    | Bật MySQL, khởi tạo database             | Docker + script trên máy | 1 lần (hoặc khi reset)       |
| 4    | Nạp tài liệu lên Qdrant                  | Máy có GPU hoặc Colab    | 1 lần (hoặc khi đổi PDF)     |
| 5    | Bật app                                  | Docker                   | Mỗi lần chạy                 |
| 6    | Kiểm tra                                 | Trình duyệt              |                              |

---

## 1. Cài công cụ và clone code

Cần có:

| Công cụ                                                   | Dùng để                                    | Kiểm tra                   |
|-----------------------------------------------------------|--------------------------------------------|----------------------------|
| [Git](https://git-scm.com/)                               | Lấy code                                   | `git --version`            |
| [Docker](https://docs.docker.com/get-docker/) + Compose v2 | Chạy MySQL, backend, frontend              | `docker compose version`   |
| [uv](https://docs.astral.sh/uv/)                          | Chạy script Python (database, tài liệu)    | `uv --version`             |

Cài uv (Linux/macOS):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Máy cần khoảng **10GB ổ trống** (image Docker, model embedding) và **4GB RAM trống** cho backend.

Clone code:

```bash
git clone https://github.com/trungtech1908/ChatBot_Haui.git
cd ChatBot_Haui
```

Mọi lệnh bên dưới đều bắt đầu từ thư mục gốc `ChatBot_Haui/` nếu không ghi khác.

---

## 2. Lấy API key và tạo `.env`

### 2.1. Lấy key

| Dịch vụ                      | Dùng để                            | Lấy key ở đâu                                                       | Bắt buộc |
|------------------------------|------------------------------------|---------------------------------------------------------------------|----------|
| Google AI Studio (Gemini)    | LLM trả lời, nếu chọn `google`     | https://aistudio.google.com/apikey                                  | Chọn 1 trong 2 |
| Groq                         | LLM trả lời, nếu chọn `groq`       | https://console.groq.com/keys                                       | Chọn 1 trong 2 |
| Qdrant Cloud                 | Lưu vector tài liệu                | https://cloud.qdrant.io: tạo cluster (gói Free đủ dùng), lấy URL và API key của cluster | ✔ |
| Cohere                       | Xếp hạng lại kết quả tìm kiếm      | https://dashboard.cohere.com/api-keys (Trial key dùng được)         | ✔ |

URL Qdrant có dạng `https://xxxxxxxx.<region>.aws.cloud.qdrant.io`.

### 2.2. Tạo file `.env`

```bash
cp .env.example .env
```

Mở `.env` và điền:

```bash
# Chuỗi bí mật để ký phiên đăng nhập, tạo bằng: openssl rand -hex 32
SECRET_KEY=dán_chuỗi_vừa_tạo

# Mật khẩu MySQL (tự đặt; Docker dùng nó làm mật khẩu root)
DB_PASSWORD=mat_khau_cua_ban

# LLM: điền key của provider đã chọn
LLM_PROVIDER=google
GOOGLE_API_KEY=...
# hoặc
# LLM_PROVIDER=groq
# GROQ_API_KEY=...

QDRANT_URL=https://...
QDRANT_API_KEY=...
COHERE_API_KEY=...
```

Các biến khác giữ mặc định. Nếu máy đã có MySQL chạy ở cổng 3306, đổi `DB_PORT=3307`; nếu cổng 8080 đã bị dùng, đổi `APP_PORT`.

> `.env` chứa key thật, đã được gitignore. Không commit, không gửi file này cho người khác.

---

## 3. Khởi tạo database

```bash
# Bật riêng MySQL, chờ tới khi sẵn sàng
docker compose up -d --wait mysql

# Tạo bảng và nạp dữ liệu mẫu từ máy
cd backend
uv sync --extra cpu
uv run python scripts/init_db.py
cd ..
```

Thấy dòng `Xong: CSDLDoAnCN @ localhost:3306` là thành công. `uv sync` lần đầu tải thư viện (~1GB) nên mất vài phút.

Chi tiết và các tùy chọn (`--reset`, `--no-seed`): [database.md](database.md).

---

## 4. Nạp tài liệu lên Qdrant

Chatbot tìm câu trả lời trong các PDF ở `backend/assets/documents/`, nên các PDF này phải được OCR, chia chunk và đẩy lên Qdrant trước.

**Bỏ qua bước này** nếu collection `QDRANT_COLLECTION` trên Qdrant Cloud đã có dữ liệu (ví dụ dùng chung cluster với người đã nạp). Kiểm tra trong trang quản lý Qdrant Cloud: collection có khoảng 170 điểm là đã nạp.

Chọn một trong hai cách:

- **Máy có GPU NVIDIA:**
  ```bash
  sudo apt install poppler-utils
  cd backend
  uv sync --extra gpu --extra ingest
  uv run python scripts/ingest.py
  cd ..
  ```
- **Không có GPU:** chạy `backend/scripts/ingest_colab.py` trên Google Colab.

Hướng dẫn đầy đủ cho cả hai cách: [ingest.md](ingest.md).

> Chạy lại `uv sync --extra cpu` trong `backend/` nếu sau đó muốn dùng lại môi trường CPU cho `init_db.py` hoặc `evaluate.py`.

---

## 5. Bật app

```bash
docker compose up -d --build
```

Lần đầu build image mất khoảng 5–10 phút. Kiểm tra trạng thái:

```bash
docker compose ps
```

Cả 3 service `mysql`, `backend`, `frontend` phải ở trạng thái `running`/`healthy`.

Lần đầu khởi động, backend tải model embedding bge-m3 (~2GB) ở nền; trong lúc đó web vẫn dùng được, nhưng câu hỏi chat đầu tiên sẽ phải chờ tải xong. Theo dõi bằng:

```bash
docker compose logs -f backend
```

Thấy dòng `Đã nạp xong RAG` là chatbot sẵn sàng. Model được lưu trong volume `hf_cache`, các lần sau không tải lại.

---

## 6. Kiểm tra

1. Mở http://localhost:8080 (hoặc cổng `APP_PORT` đã đặt).
2. Đăng nhập bằng tài khoản mẫu: `SV001_tk` / `pass001` (có `SV001_tk` … `SV010_tk`, mật khẩu `pass001` … `pass010`).
3. Xem các trang Trang chủ, Hồ sơ, Lịch học, Kết quả học tập… phải có dữ liệu.
4. Vào **Trợ lý AI**, hỏi thử: *"Cần bao nhiêu tín chỉ để được tốt nghiệp?"* Câu trả lời hiện dần từng chữ là toàn bộ hệ thống đã chạy.

Kiểm tra nhanh API: http://localhost:8080/api/health trả về `{"status":"ok"}`.

---

## Vận hành hằng ngày

| Việc                                   | Lệnh                                                        |
|----------------------------------------|-------------------------------------------------------------|
| Bật app                                | `docker compose up -d`                                      |
| Tắt app (giữ dữ liệu)                  | `docker compose down`                                       |
| Xem log                                | `docker compose logs -f backend` (hoặc `frontend`, `mysql`) |
| Cập nhật code mới                      | `git pull` rồi `docker compose up -d --build`               |
| Có migration mới sau khi pull          | `cd backend && uv sync --extra cpu && uv run python scripts/init_db.py --no-seed` |
| Đổi `.env`                             | `docker compose up -d` (tự tạo lại container đọc cấu hình mới) |
| Xóa sạch dữ liệu MySQL, làm lại bước 3 | `docker compose down -v` (xóa luôn cache model `hf_cache`)  |
| Đánh giá chất lượng chatbot            | Xem [evaluate.md](evaluate.md)                              |

---

## Lỗi thường gặp

| Hiện tượng                                               | Nguyên nhân / cách xử lý                                                                 |
|----------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `docker compose` báo `Cần DB_PASSWORD` / `Cần SECRET_KEY` | Chưa tạo `.env` hoặc chưa điền biến đó                                                    |
| `port is already allocated` khi bật MySQL hoặc app       | Cổng đã bị chiếm: đổi `DB_PORT` hoặc `APP_PORT` trong `.env`                              |
| `init_db.py` báo `Access denied for user 'root'`         | `DB_PASSWORD` khác mật khẩu lúc tạo MySQL lần đầu: `docker compose down -v` rồi làm lại bước 3 |
| Đăng nhập báo sai mật khẩu với tài khoản mẫu             | Chưa seed dữ liệu: chạy lại `init_db.py`                                                  |
| Trang web trắng / lỗi 502                                | Backend chưa `healthy`: xem `docker compose logs backend`                                |
| Chat trả lời "Xin lỗi, hệ thống đang gặp sự cố"          | Sai hoặc thiếu key LLM/Qdrant/Cohere: xem `docker compose logs backend`, sửa `.env`, `docker compose up -d` |
| Chat trả lời chung chung, không đúng quy chế             | Collection Qdrant chưa có dữ liệu hoặc sai `QDRANT_COLLECTION`: làm bước 4               |
| Log backend có `Không nạp được RAG`                      | Thiếu/sai key LLM hoặc Qdrant trong `.env`; dòng lỗi ngay bên dưới ghi rõ key nào         |
| Câu chat đầu tiên rất lâu                                | Backend đang tải model bge-m3 lần đầu, chờ log `Đã nạp xong RAG`                          |

---

## Phát triển (không dùng Docker cho backend/frontend)

Dùng khi sửa code và muốn tự reload. Cần MySQL đang chạy (bước 3) và Node.js 22+.

```bash
# Terminal 1: backend tại http://localhost:8000, tài liệu API tại http://localhost:8000/docs
cd backend
uv sync --extra cpu
uv run uvicorn chatbot_haui.main:app --reload

# Terminal 2: frontend tại http://localhost:5173 (tự chuyển /api sang backend)
cd frontend
npm install
npm run dev
```

Chạy test trước khi commit:

```bash
cd backend && uv run pytest
cd frontend && npm run lint && npm run build
```
