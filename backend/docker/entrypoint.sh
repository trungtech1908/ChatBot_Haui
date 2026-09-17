#!/bin/sh
set -e

# Cập nhật schema và nạp dữ liệu mẫu (bỏ qua bảng đã có dữ liệu)
alembic upgrade head
python scripts/seed.py

exec uvicorn chatbot_haui.main:app --host 0.0.0.0 --port 8000 --proxy-headers --workers "${WEB_CONCURRENCY:-1}"
