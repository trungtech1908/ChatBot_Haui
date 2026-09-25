# ChatBot HaUI

Hệ thống quản lý sinh viên HaUI tích hợp chatbot hỏi đáp quy chế, kết hợp văn bản quy định (RAG) với dữ liệu cá nhân của chính sinh viên đang đăng nhập (Text2SQL).

- **Backend:** FastAPI, SQLAlchemy + Alembic (PostgreSQL), JWT, LangGraph Planner–Executor (Gemini + Groq), Qdrant Cloud (hybrid dense + BM25), Cohere rerank, Mem0 (bộ nhớ dài hạn), Langfuse (trace)
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, TanStack Query

**Lần đầu chạy dự án?** Làm theo [docs/getting-started.md](docs/getting-started.md).

## Luồng chatbot

```
câu hỏi → Rewriter → Router ─┬─ chào hỏi / ngoài phạm vi / hỏi lại → trả lời trực tiếp
                              └─ tra cứu → Memory Read → Planner → Executor ─┬─ RAG (quy chế)
                                                                              ├─ Text2SQL (dữ liệu của chính SV)
                                                                              └─ Compute (phép tính)
                                          → Aggregator → Generator → Validator → trả lời | lập lại | viết lại | fallback
sau khi trả lời (chạy nền) → Memory Write
```

Text2SQL chỉ nhìn thấy schema `chatbot` (27 view tự lọc theo sinh viên đang đăng nhập), chạy bằng role chỉ-đọc riêng trong transaction `READ ONLY`; mã sinh viên lấy từ phiên đăng nhập, không bao giờ đi qua prompt.

## Cấu trúc

```
backend/
  alembic/                  Migration (schema core/private/chatbot, view, role)
  assets/
    documents/              PDF nguồn của RAG
    seed/                   02_seed_tham_so.sql (tham số từ văn bản), 04_sample_data.sql (62 SV giả lập)
    chunks.json             Chunk văn bản đã OCR, để index lại không cần GPU
  docker/                   Dockerfile backend (chỉ chạy API)
  scripts/
    init_db.py              Tạo database, migrate, nạp dữ liệu mẫu (docs/database.md)
    gen_sample_data.py      Sinh 04_sample_data.sql (tất định)
    ingest.py               OCR → chunk (assets/chunks.json) → Qdrant hybrid dense + BM25 (docs/ingest.md)
    ingest_colab.py         Bản của ingest.py chạy trên Google Colab
    evaluate.py             Đánh giá chatbot trên bộ câu hỏi (docs/evaluate.md)
  src/chatbot_haui/
    main.py                 FastAPI + checkpointer LangGraph (Postgres)
    ai/                     graph, state, llm, memory (Mem0), observability (Langfuse), documents
      nodes/                conversation (rewriter, router, direct, finalize), planning, executor, answering
      tools/                rag, sparse (BM25), text2sql, sql_guard, compute
      prompts/              prompt từng bước
    api/                    deps, routes: auth, students, chat
    core/                   config (đọc .env), security (JWT, argon2)
    db/                     session (2 engine: owner / chatbot_reader), models, sql/views.sql
    schema/                 Pydantic schema request/response
    services/               auth, student, chat
  tests/                    pytest trên PostgreSQL thật, không gọi API ngoài
frontend/
  src/                      api, components, features (mỗi màn hình một thư mục), lib, types
docs/                       Hướng dẫn chạy, database, nạp tài liệu, đánh giá
docker-compose.yml          postgres + backend + frontend
```

## Cấu hình

Copy `.env.example` thành `.env` ở thư mục gốc rồi điền. Nhóm biến chính:

| Nhóm | Biến |
|---|---|
| Bảo mật | `SECRET_KEY` (`openssl rand -hex 32`) |
| PostgreSQL | `DB_*`; `DB_CHATBOT_USER`, `DB_CHATBOT_PASSWORD` cho role Text2SQL |
| LLM | `LLM_PROVIDER` + model chính; `LLM_PROVIDER_SMALL`, `LLM_MODEL_SMALL` cho bước nhỏ; `GOOGLE_API_KEY`, `GROQ_API_KEY` |
| RAG | `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION` (văn bản, hybrid), `COHERE_API_KEY` |
| Bộ nhớ | `MEMORY_SALT` (`openssl rand -hex 32`), `QDRANT_MEMORY_COLLECTION`, `MEMORY_ENABLED` |
| Trace | `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_ENABLED` |
| Khác | `DATA_AS_OF` (ngày chốt dữ liệu nêu trong câu trả lời) |

Khi cả hai key LLM đều có, mỗi cỡ model tự chuyển sang provider còn lại nếu provider chính quá tải hoặc hết quota.

## Chạy bằng Docker

```bash
# 1. Bật PostgreSQL và khởi tạo database (docs/database.md)
docker compose up -d --wait postgres
cd backend && uv sync --extra cpu && uv run --no-sync python scripts/init_db.py && cd ..

# 2. Bật app
docker compose up -d --build
```

Mở http://localhost:8080. Tài khoản mẫu: **tên đăng nhập = mật khẩu = mã sinh viên**, ví dụ `2024619567`. Danh sách sinh viên theo tình huống kiểm thử: [docs/database.md](docs/database.md#dữ-liệu-giả-lập).

Chatbot cần tài liệu đã có trên Qdrant, xem [docs/ingest.md](docs/ingest.md).

## Phát triển local

Luôn dùng `uv run --no-sync` sau khi đã `uv sync --extra cpu`: `uv run` không kèm extra sẽ tự sync lại và kéo torch bản CUDA (~3GB).

```bash
# Backend: http://localhost:8000, API docs tại /docs
cd backend
uv sync --extra cpu
uv run --no-sync python scripts/init_db.py
uv run --no-sync uvicorn chatbot_haui.main:app --reload

# Frontend: http://localhost:5173 (tự chuyển /api sang backend)
cd frontend
npm install
npm run dev
```

Test và kiểm tra (test backend cần PostgreSQL đang chạy; tự tạo database `<DB_NAME>_test`):

```bash
cd backend && uv run --no-sync pytest
cd frontend && npm run lint && npm run build
```

## Tài liệu hướng dẫn

- Chạy dự án từ đầu: [docs/getting-started.md](docs/getting-started.md)
- Khởi tạo database, dữ liệu giả lập: [docs/database.md](docs/database.md)
- Nạp tài liệu lên Qdrant: [docs/ingest.md](docs/ingest.md)
- Đánh giá chatbot: [docs/evaluate.md](docs/evaluate.md)
