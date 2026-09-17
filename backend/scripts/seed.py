"""Nạp dữ liệu mẫu vào MySQL. Chạy từ backend/: uv run python scripts/seed.py"""
import logging

from chatbot_haui.db.seed import seed_database
from chatbot_haui.db.session import SessionLocal

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    with SessionLocal() as db:
        seed_database(db)
