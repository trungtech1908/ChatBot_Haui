"""chat_conversation: chia lịch sử chat thành nhiều cuộc trò chuyện

Tin nhắn cũ của mỗi tài khoản gộp thành một cuộc trò chuyện (tiêu đề = câu hỏi đầu tiên). Bộ nhớ phiên của
graph trước đây có thread_id = tên đăng nhập, nay là id cuộc trò chuyện: chuyển luôn các checkpoint cũ sang
cuộc trò chuyện đó để không mất ngữ cảnh. Bảng checkpoint do LangGraph tự tạo lúc app chạy, có thể chưa có.

Revision ID: a1c3e5f70b21
Revises: c996469711a7
Create Date: 2026-09-26 12:00:00
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'a1c3e5f70b21'
down_revision: str | None = 'c996469711a7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CHECKPOINT_TABLES = ("checkpoints", "checkpoint_blobs", "checkpoint_writes")
TITLE_LEN = 60


def upgrade() -> None:
    op.create_table(
        'chat_conversation',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['username'], ['private.tai_khoan.ten_dn'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chat_conversation_username'), 'chat_conversation', ['username'], unique=False)
    op.add_column('chat_message', sa.Column('conversation_id', sa.String(length=36), nullable=True))

    bind = op.get_bind()
    bind.execute(sa.text("""
        INSERT INTO chat_conversation (id, username, title, created_at, updated_at)
        SELECT gen_random_uuid()::text, m.username,
               COALESCE(NULLIF(left((SELECT f.content FROM chat_message f
                                     WHERE f.username = m.username AND f.role = 'user'
                                     ORDER BY f.id LIMIT 1), :n), ''), 'Cuộc trò chuyện'),
               min(m.created_at), max(m.created_at)
        FROM chat_message m GROUP BY m.username"""), {"n": TITLE_LEN})
    bind.execute(sa.text("""
        UPDATE chat_message m SET conversation_id = c.id FROM chat_conversation c WHERE c.username = m.username"""))
    for table in CHECKPOINT_TABLES:
        if bind.execute(sa.text("SELECT to_regclass(:t)"), {"t": f"public.{table}"}).scalar():
            bind.execute(sa.text(f"""
                UPDATE public.{table} t SET thread_id = c.id FROM chat_conversation c WHERE t.thread_id = c.username"""))

    op.alter_column('chat_message', 'conversation_id', nullable=False)
    op.create_foreign_key('fk_chat_message_conversation', 'chat_message', 'chat_conversation',
                          ['conversation_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_chat_message_conversation_id'), 'chat_message', ['conversation_id'], unique=False)


def downgrade() -> None:
    # Checkpoint của các cuộc trò chuyện không gộp lại được thành một thread/tài khoản: bỏ đi
    bind = op.get_bind()
    for table in CHECKPOINT_TABLES:
        if bind.execute(sa.text("SELECT to_regclass(:t)"), {"t": f"public.{table}"}).scalar():
            bind.execute(sa.text(f"DELETE FROM public.{table} WHERE thread_id IN (SELECT id FROM chat_conversation)"))
    op.drop_index(op.f('ix_chat_message_conversation_id'), table_name='chat_message')
    op.drop_constraint('fk_chat_message_conversation', 'chat_message', type_='foreignkey')
    op.drop_column('chat_message', 'conversation_id')
    op.drop_index(op.f('ix_chat_conversation_username'), table_name='chat_conversation')
    op.drop_table('chat_conversation')
