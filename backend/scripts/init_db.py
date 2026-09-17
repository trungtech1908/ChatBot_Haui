"""Khởi tạo database: tạo database (nếu chưa có) -> chạy migration -> nạp dữ liệu mẫu.

Chạy từ backend/ (MySQL phải đang chạy, cấu hình trong .env):
    uv run python scripts/init_db.py              # tạo + migrate + seed
    uv run python scripts/init_db.py --no-seed    # chỉ tạo + migrate
    uv run python scripts/init_db.py --reset      # xóa sạch database rồi tạo lại từ đầu
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)  # để đọc đúng .env, alembic.ini, assets/seed dù chạy từ đâu

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402

from chatbot_haui.core.config import settings  # noqa: E402
from chatbot_haui.db.seed import seed_database  # noqa: E402
from chatbot_haui.db.session import SessionLocal  # noqa: E402

logger = logging.getLogger("init_db")


def wait_for_server(retries: int = 30):
    """Chờ MySQL sẵn sàng (container vừa khởi động cần vài giây)."""
    engine = create_engine(settings.db_server_url())
    try:
        for attempt in range(1, retries + 1):
            try:
                with engine.connect():
                    return engine
            except OperationalError as e:
                if attempt == retries:
                    raise SystemExit(f"Không kết nối được MySQL {settings.db_host}:{settings.db_port}: {e.orig}") from e
                logger.info("Chờ MySQL %s:%s... (%d/%d)", settings.db_host, settings.db_port, attempt, retries)
                time.sleep(2)
    finally:
        engine.dispose()


def create_database(reset: bool):
    engine = create_engine(settings.db_server_url())
    with engine.connect() as conn:
        if reset:
            conn.execute(text(f"DROP DATABASE IF EXISTS `{settings.db_name}`"))
            logger.info("Đã xóa database %s", settings.db_name)
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{settings.db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    engine.dispose()
    logger.info("Database %s đã sẵn sàng", settings.db_name)


def main():
    parser = argparse.ArgumentParser(description="Khởi tạo database cho backend")
    parser.add_argument("--no-seed", action="store_true", help="không nạp dữ liệu mẫu")
    parser.add_argument("--reset", action="store_true", help="xóa sạch database trước khi tạo lại")
    parser.add_argument("-y", "--yes", action="store_true", help="không hỏi xác nhận khi --reset")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    target = f"{settings.db_name} @ {settings.db_host}:{settings.db_port}"
    if args.reset and not args.yes:
        if input(f"Xóa toàn bộ dữ liệu trong {target}? Gõ 'yes' để tiếp tục: ").strip() != "yes":
            sys.exit("Đã hủy.")

    wait_for_server()
    create_database(args.reset)

    logger.info("Chạy migration...")
    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")

    if not args.no_seed:
        logger.info("Nạp dữ liệu mẫu từ %s...", settings.seed_dir)
        with SessionLocal() as db:
            seed_database(db)

    logger.info("Xong: %s", target)


if __name__ == "__main__":
    main()
