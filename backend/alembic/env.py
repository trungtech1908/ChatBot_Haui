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


def run_migrations_offline():
    context.configure(url=settings.db_url, target_metadata=Base.metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_engine(settings.db_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
