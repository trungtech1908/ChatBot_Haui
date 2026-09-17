import os

os.environ["RAG_PRELOAD"] = "false"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes!!"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from chatbot_haui.db import models  # noqa: F401
from chatbot_haui.db.seed import seed_database
from chatbot_haui.db.session import Base, get_db
from chatbot_haui.main import app
from chatbot_haui.services import chat as chat_service


@pytest.fixture(scope="session")
def session_factory(tmp_path_factory):
    # SQLite + dữ liệu seed thật, không cần MySQL
    engine = create_engine(f"sqlite:///{tmp_path_factory.mktemp('db') / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    with factory() as db:
        seed_database(db)
    return factory


@pytest.fixture
def client(session_factory, monkeypatch):
    def override_db():
        with session_factory() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(chat_service, "SessionLocal", session_factory)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    token = client.post("/api/auth/login", json={"username": "SV001_tk", "password": "pass001"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
