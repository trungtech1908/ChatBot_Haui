"""Khởi tạo database: tạo database (nếu chưa có) -> chạy migration -> nạp dữ liệu mẫu.

Chạy từ backend/ (PostgreSQL phải đang chạy, cấu hình trong .env):
    uv run --no-sync python scripts/init_db.py              # tạo + migrate + seed
    uv run --no-sync python scripts/init_db.py --no-seed    # chỉ tạo + migrate
    uv run --no-sync python scripts/init_db.py --reset      # xóa sạch database rồi tạo lại từ đầu

Dữ liệu mẫu (assets/seed):
    02_seed_tham_so.sql  tham số lấy từ văn bản quy chế (thang điểm, đơn giá, khoản thu, ...)
    04_sample_data.sql   62 sinh viên giả lập, sinh bởi scripts/gen_sample_data.py
                         Mật khẩu mỗi tài khoản = mã sinh viên.
"""
import argparse
import logging
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
os.chdir(BACKEND_DIR)  # để đọc đúng .env, alembic.ini, assets/seed dù chạy từ đâu

import psycopg  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from psycopg import sql  # noqa: E402

from chatbot_haui.core.config import settings  # noqa: E402

logger = logging.getLogger("init_db")
SEED_DIR = BACKEND_DIR / "assets" / "seed"
SEED_FILES = ["02_seed_tham_so.sql", "04_sample_data.sql"]


def connect(database: str, autocommit: bool = False) -> psycopg.Connection:
    return psycopg.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user, password=settings.db_password,
        dbname=database, autocommit=autocommit,
    )


def wait_for_server(retries: int = 30):
    """Chờ PostgreSQL sẵn sàng (container vừa khởi động cần vài giây)."""
    for attempt in range(1, retries + 1):
        try:
            connect("postgres").close()
            return
        except psycopg.OperationalError as e:
            if attempt == retries:
                raise SystemExit(f"Không kết nối được PostgreSQL {settings.db_host}:{settings.db_port}: {e}") from e
            logger.info("Chờ PostgreSQL %s:%s... (%d/%d)", settings.db_host, settings.db_port, attempt, retries)
            time.sleep(2)


def create_database(reset: bool):
    # CREATE/DROP DATABASE không chạy được trong transaction
    with connect("postgres", autocommit=True) as conn:
        name = sql.Identifier(settings.db_name)
        if reset:
            conn.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                         (settings.db_name,))
            conn.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(name))
            logger.info("Đã xóa database %s", settings.db_name)
        if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (settings.db_name,)).fetchone():
            conn.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(name))
    logger.info("Database %s đã sẵn sàng", settings.db_name)


def seed():
    with connect(settings.db_name) as conn:
        if conn.execute("SELECT 1 FROM core.sinh_vien LIMIT 1").fetchone():
            logger.info("Đã có dữ liệu, bỏ qua nạp dữ liệu mẫu (dùng --reset để nạp lại)")
            return
        for name in SEED_FILES:
            logger.info("Nạp %s...", name)
            # Không truyền tham số → psycopg gửi nguyên văn, ký tự % trong dữ liệu không bị hiểu là placeholder
            conn.execute((SEED_DIR / name).read_text(encoding="utf-8"))
        conn.execute("RESET search_path")
        counts = conn.execute(
            "SELECT (SELECT count(*) FROM core.sinh_vien), (SELECT count(*) FROM private.tai_khoan), "
            "(SELECT count(*) FROM core.diem_hp), (SELECT count(*) FROM core.lich_hoc)"
        ).fetchone()
        logger.info("Đã nạp: %d sinh viên, %d tài khoản, %d điểm học phần, %d buổi lịch học", *counts)


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
        seed()

    logger.info("Xong: %s", target)


if __name__ == "__main__":
    main()
