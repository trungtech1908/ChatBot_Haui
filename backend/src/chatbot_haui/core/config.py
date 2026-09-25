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

    # --- PostgreSQL ---
    # db_user là owner: tạo schema/bảng/view, phục vụ auth và API sinh viên
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "postgres"
    db_password: str = "123456"
    db_name: str = "CSDLDoAnCN"
    # Role riêng cho Text2SQL: chỉ SELECT trên schema chatbot
    db_chatbot_user: str = "chatbot_app"
    db_chatbot_password: str = "chatbot-app-123456"

    # --- LLM ---
    llm_provider: Literal["google", "groq"] = "google"
    google_api_key: str | None = None
    google_model: str = "gemini-2.5-flash"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    # Model nhỏ cho rewriter/router/judge/memory; có thể ở provider khác model chính để chia quota.
    # Để trống → cùng provider với model chính / model nhỏ mặc định của provider đó.
    llm_provider_small: Literal["google", "groq"] | None = None
    llm_model_small: str | None = None

    # --- Retrieval ---
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "haui_quy_che_hybrid"
    qdrant_memory_collection: str = "haui_chatbot_memory"
    cohere_api_key: str | None = None
    embedding_model: str = "BAAI/bge-m3"
    rag_preload: bool = True  # nạp sẵn RAG khi khởi động

    # Thời điểm chốt dữ liệu, nêu trong câu trả lời có số liệu cá nhân (DB có thể là bản sao đồng bộ trễ).
    # Để trống → ngày hiện tại.
    data_as_of: str | None = None

    # --- Bộ nhớ dài hạn (Mem0 OSS in-process) ---
    memory_enabled: bool = True
    memory_salt: str = ""

    # --- Langfuse ---
    langfuse_enabled: bool = True
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"

    # --- Đường dẫn, tương đối với thư mục backend/ ---
    documents_dir: Path = Path("assets/documents")

    @field_validator(
        "google_api_key", "groq_api_key", "qdrant_url", "qdrant_api_key", "cohere_api_key",
        "langfuse_public_key", "langfuse_secret_key", "llm_model_small", "llm_provider_small", "data_as_of",
        mode="before",
    )
    @classmethod
    def empty_as_none(cls, value):
        # Biến để trống trong .env coi như không đặt
        return value or None

    @property
    def langfuse_ready(self) -> bool:
        return bool(self.langfuse_enabled and self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def memory_ready(self) -> bool:
        return bool(self.memory_enabled and self.memory_salt and self.qdrant_url and self.qdrant_api_key)

    def db_server_url(self, database: str | None = None) -> str:
        """URL của owner. database=None → nối tới 'postgres' để tạo/xóa database khác."""
        return self._url(self.db_user, self.db_password, database or "postgres")

    @property
    def db_url(self) -> str:
        return self._url(self.db_user, self.db_password, self.db_name)

    @property
    def db_chatbot_url(self) -> str:
        """Kết nối dành riêng cho Text2SQL: role chatbot_reader, chỉ thấy schema chatbot."""
        return self._url(self.db_chatbot_user, self.db_chatbot_password, self.db_name)

    def _url(self, user: str, password: str, database: str) -> str:
        # URL.create tự escape ký tự đặc biệt trong mật khẩu
        return URL.create(
            "postgresql+psycopg", user, password, self.db_host, self.db_port, database,
        ).render_as_string(hide_password=False)


settings = Settings()
