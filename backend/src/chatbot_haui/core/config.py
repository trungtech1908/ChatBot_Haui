"""Toàn bộ cấu hình backend, đọc từ biến môi trường hoặc file .env."""
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Settings(BaseSettings):
    # Chạy từ backend/ hoặc thư mục gốc repo đều đọc được .env ở gốc
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # --- Bảo mật ---
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60 * 24

    # --- MySQL ---
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str = "123456"
    db_name: str = "CSDLDoAnCN"

    # --- LLM ---
    llm_provider: Literal["google", "groq"] = "google"
    google_api_key: str | None = None
    google_model: str = "gemini-2.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Retrieval ---
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "RAG_ChatBot_HAUI"
    cohere_api_key: str | None = None
    embedding_model: str = "BAAI/bge-m3"
    rag_preload: bool = True  # nạp sẵn RAG khi khởi động

    # --- Đường dẫn, tương đối với thư mục backend/ ---
    seed_dir: Path = Path("assets/seed")
    documents_dir: Path = Path("assets/documents")

    @field_validator("google_api_key", "groq_api_key", "qdrant_url", "qdrant_api_key", "cohere_api_key", mode="before")
    @classmethod
    def empty_as_none(cls, value):
        # Biến để trống trong .env coi như không đặt
        return value or None

    def db_server_url(self, database: str | None = None) -> str:
        # URL.create tự escape ký tự đặc biệt trong mật khẩu
        return URL.create(
            "mysql+pymysql", self.db_user, self.db_password, self.db_host, self.db_port, database,
            query={"charset": "utf8mb4"},
        ).render_as_string(hide_password=False)

    @property
    def db_url(self) -> str:
        return self.db_server_url(self.db_name)


settings = Settings()
