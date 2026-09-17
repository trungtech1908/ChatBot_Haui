# syntax=docker/dockerfile:1
# Build từ thư mục backend/: docker build -f docker/Dockerfile .
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
WORKDIR /app

# Cài dependency trước (layer cache), torch bản CPU cho embedding
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --extra cpu --no-install-project

COPY pyproject.toml uv.lock ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra cpu --no-editable


FROM python:3.12-slim-bookworm

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/cache/huggingface

RUN useradd --create-home app && mkdir -p /cache/huggingface && chown app:app /cache/huggingface

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv

USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

# Database (migration, dữ liệu mẫu) khởi tạo ngoài Docker bằng scripts/init_db.py
# 1 worker mặc định: model embedding nạp riêng cho từng worker, tốn RAM
CMD ["sh", "-c", "exec uvicorn chatbot_haui.main:app --host 0.0.0.0 --port 8000 --proxy-headers --workers ${WEB_CONCURRENCY:-1}"]
