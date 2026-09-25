"""Fixture chung.

Test DB dùng PostgreSQL thật (view, set_config, role chatbot_reader không giả lập được bằng SQLite):
database riêng `<DB_NAME>_test` được tạo mới mỗi phiên test bằng đúng migration + dữ liệu mẫu của app.
Không kết nối được PostgreSQL → các test cần DB bị skip, test thuần logic vẫn chạy.
Không test nào gọi API ngoài (LLM, Qdrant, Cohere, Langfuse).
"""
import os

os.environ["RAG_PRELOAD"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes!!"
os.environ["LANGFUSE_ENABLED"] = "false"
os.environ["MEMORY_ENABLED"] = "false"
os.environ["MEMORY_SALT"] = "test-salt"
# Phải đặt TRƯỚC khi import chatbot_haui: settings và engine được tạo lúc import
from chatbot_haui.core.config import Settings  # noqa: E402

os.environ["DB_NAME"] = f"{Settings().db_name}_test"

import psycopg  # noqa: E402
import pytest  # noqa: E402

from chatbot_haui.core.config import settings  # noqa: E402

STUDENT = "2024619567"  # khuyết tật: miễn học phí, nhận HB NTB (ARCHITECTURE mục 7)


def _postgres_available() -> bool:
    try:
        psycopg.connect(host=settings.db_host, port=settings.db_port, user=settings.db_user,
                        password=settings.db_password, dbname="postgres", connect_timeout=3).close()
        return True
    except psycopg.OperationalError:
        return False


@pytest.fixture(scope="session")
def database():
    if not _postgres_available():
        pytest.skip("Không có PostgreSQL cho test")
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location("init_db", Path(__file__).parents[1] / "scripts" / "init_db.py")
    init_db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(init_db)

    init_db.create_database(reset=True)
    from alembic import command
    from alembic.config import Config
    command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")
    init_db.seed()
    yield settings.db_name


@pytest.fixture
def client(database):
    from fastapi.testclient import TestClient

    from chatbot_haui.main import app
    with TestClient(app) as c:  # chạy lifespan: checkpointer Postgres + graph
        yield c


@pytest.fixture
def auth_headers(client):
    token = client.post("/api/auth/login", json={"username": STUDENT, "password": STUDENT}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
