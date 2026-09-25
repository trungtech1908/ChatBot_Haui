import logging
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from chatbot_haui.core.config import settings
from chatbot_haui.db import models  # noqa: F401  đăng ký toàn bộ bảng vào metadata
from chatbot_haui.db.session import Base

# Script gọi alembic (init_db.py) đã tự cấu hình logging thì giữ nguyên
if context.config.config_file_name and not logging.getLogger().handlers:
    fileConfig(context.config.config_file_name)

# Schema do Alembic quản lý. chatbot chỉ chứa view (tạo bằng db/sql/views.sql), không so sánh.
MANAGED_SCHEMAS = {"core", "private", None}
# Bảng trong schema public do app quản lý; bảng khác (checkpointer LangGraph tự tạo) bỏ qua
MANAGED_PUBLIC_TABLES = {"chat_message"}


def include_name(name, type_, parent_names) -> bool:
    if type_ == "schema":
        return name in MANAGED_SCHEMAS
    return True


def include_object(obj, name, type_, reflected, compare_to) -> bool:
    # Không để autogenerate sinh DROP TABLE cho bảng của LangGraph checkpointer
    if type_ == "table" and obj.schema in (None, "public"):
        return name in MANAGED_PUBLIC_TABLES
    return True


CONFIGURE = dict(
    target_metadata=Base.metadata,
    compare_type=True,
    include_schemas=True,
    include_name=include_name,
    include_object=include_object,
)


def run_migrations_offline():
    context.configure(url=settings.db_url, literal_binds=True, **CONFIGURE)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(settings.db_url)
    with engine.connect() as connection:
        context.configure(connection=connection, **CONFIGURE)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
