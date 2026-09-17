"""Toàn bộ cấu hình backend, đọc từ biến môi trường hoặc file .env."""
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


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

    @property
    def db_url(self) -> str:
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


settings = Settings()
