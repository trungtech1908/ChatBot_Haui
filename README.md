# ChatBot HaUI

Hệ thống quản lý sinh viên HaUI tích hợp chatbot RAG tra cứu quy chế, quy định, học phí.

- **Backend:** FastAPI, SQLAlchemy + Alembic (MySQL), JWT, LangGraph RAG (Gemini/Groq, Qdrant Cloud, Cohere rerank)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query

## Cấu trúc

```
backend/
  alembic/                  Migration database
  assets/
    documents/              PDF nguồn của RAG
    seed/                   JSON dữ liệu mẫu
  docker/                   Dockerfile, entrypoint (migrate → seed → uvicorn)
  scripts/
    ingest.py               OCR → chia chunk → Qdrant (chạy tay, xem docs/ingest.md)
    ingest_colab.py         Bản độc lập của ingest.py để copy chạy trên Google Colab
    evaluate.py             Đánh giá RAG (chạy tay, xem docs/evaluate.md)
    seed.py                 Nạp dữ liệu mẫu
  src/chatbot_haui/
    main.py                 Khởi tạo FastAPI
    ai/                     RAG: llm, graph, nodes, prompts; text_to_sql (thử nghiệm)
    api/                    deps (DB session, user hiện tại), routes: auth, students, chat
    core/                   config (đọc .env), security (JWT, hash mật khẩu)
    db/                     session, models (student, academic, internship, finance, chat), seed
    schema/                 Pydantic schema request/response
    services/               Logic nghiệp vụ: auth, student, chat
  tests/
frontend/
  src/
    api/                    Gọi backend (auth, students, chat stream)
    components/             layout (Header, Sidebar), ui dùng chung
    features/               Mỗi màn hình một thư mục: auth, profile, curriculum, schedule,
                            exams, internship, grades, academic, finance, chat
    lib/                    api client, format
    types/                  Kiểu dữ liệu API
  nginx.conf                Phục vụ SPA, chuyển /api sang backend
docs/                       Hướng dẫn nạp tài liệu, đánh giá RAG
docker-compose.yml          mysql + backend + frontend
```

## Cấu hình

Copy `.env.example` thành `.env` ở thư mục gốc rồi điền:

- `SECRET_KEY`: ký JWT, tạo bằng `openssl rand -hex 32`
- LLM: `LLM_PROVIDER=google` (cần `GOOGLE_API_KEY`) hoặc `groq` (cần `GROQ_API_KEY`)
- Qdrant Cloud: `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`
- Rerank: `COHERE_API_KEY`

## Chạy bằng Docker

```bash
docker compose up -d --build
```

Mở http://localhost:8080. Backend tự chạy migration và nạp dữ liệu mẫu khi khởi động. Lần đầu backend tải model bge-m3 (~2GB) vào volume `hf_cache`.

Tài khoản mẫu: `SV001_tk` / `pass001` (tới `SV010_tk` / `pass010`).

Dữ liệu tài liệu phải có sẵn trên Qdrant, xem [docs/ingest.md](docs/ingest.md).

## Phát triển local

Cần MySQL đang chạy theo `.env`.

```bash
# Backend: http://localhost:8000, API docs tại /docs
cd backend
uv sync --extra cpu
uv run alembic upgrade head
uv run python scripts/seed.py
uv run uvicorn chatbot_haui.main:app --reload

# Frontend: http://localhost:5173 (tự chuyển /api sang backend)
cd frontend
npm install
npm run dev
```

Test và kiểm tra:

```bash
cd backend && uv run pytest
cd frontend && npm run lint && npm run build
```

Đổi model database: sửa `backend/src/chatbot_haui/db/models/`, rồi `uv run alembic revision --autogenerate -m "mô tả"` và `uv run alembic upgrade head`.

## Script RAG (ngoài Docker)

- Nạp tài liệu lên Qdrant (trên máy hoặc Google Colab): [docs/ingest.md](docs/ingest.md)
- Đánh giá chất lượng RAG: [docs/evaluate.md](docs/evaluate.md)
