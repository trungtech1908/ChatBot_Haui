"""Tool Text2SQL (ARCHITECTURE mục 2.7).

Sinh SQL → kiểm tra (sql_guard) → chạy trong transaction READ ONLY đã gắn app.ma_sv (chatbot_scope)
bằng role chatbot_reader. Lỗi thì đưa thông báo đã rút gọn lại cho LLM sinh lại, tối đa 2 lần.
Lỗi thô không bao giờ trả cho người dùng (làm lộ cấu trúc schema) — chỉ ghi log phía server.
"""
import asyncio
import datetime as dt
import logging
from decimal import Decimal
from functools import lru_cache
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from sqlalchemy import text

from chatbot_haui.ai.llm import structured
from chatbot_haui.ai.prompts import text2sql as prompts
from chatbot_haui.ai.tools.sql_guard import MAX_ROWS, SqlRejected, check
from chatbot_haui.db.session import chatbot_scope, engine

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
# Không gửi định danh sinh viên sang LLM ngoài (ARCHITECTURE mục 6)
HIDDEN_COLUMNS = {"ma_sv", "ho_ten"}


class SqlDraft(BaseModel):
    sql: str = Field(default="", description="Một câu SELECT PostgreSQL; để trống nếu không hỗ trợ")
    khong_ho_tro: Literal["", "nguoi_khac", "khong_co_du_lieu"] = Field(
        default="", description="Lý do không sinh SQL; để trống nếu đã sinh SQL")
    gia_dinh: str = Field(default="", description="Cách hiểu đã chọn khi câu hỏi mơ hồ")


@lru_cache
def view_columns() -> dict[str, list[tuple[str, str]]]:
    """Cột + kiểu của mọi view trong schema chatbot, đọc từ information_schema (nguồn sự thật là DB)."""
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT table_name, column_name, data_type FROM information_schema.columns
            WHERE table_schema = 'chatbot' ORDER BY table_name, ordinal_position"""))
        out: dict[str, list[tuple[str, str]]] = {}
        for table, column, data_type in rows:
            out.setdefault(table, []).append((column, data_type))
    return out


def schema_context() -> str:
    lines = []
    for view, cols in view_columns().items():
        doc = prompts.VIEW_DOCS.get(view, "")
        lines.append(f"- chatbot.{view} — {doc}\n  Cột: " + ", ".join(f"{c} {t}" for c, t in cols))
    return "\n".join(lines)


@lru_cache
def _chain():
    prompt = ChatPromptTemplate.from_messages([("system", prompts.SYSTEM), ("human", prompts.HUMAN)])
    return prompt | structured("main", SqlDraft)


def _jsonable(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value


def _execute(ma_sv: str, sql: str) -> tuple[list[str], list[dict]]:
    with chatbot_scope(ma_sv) as conn:
        # Chạy qua cursor của driver, không qua sqlalchemy.text(): chuỗi ':abc' trong literal
        # sẽ bị text() hiểu nhầm là bind parameter
        cursor = conn.connection.driver_connection.cursor()
        cursor.execute(sql)
        columns = [d.name for d in cursor.description]
        rows = cursor.fetchmany(MAX_ROWS)
    keep = [c for c in columns if c not in HIDDEN_COLUMNS]
    return keep, [{c: _jsonable(v) for c, v in zip(columns, r) if c in keep} for r in rows]


def _short_error(e: Exception) -> str:
    # Chỉ dòng đầu (VD: column "x" does not exist) — đủ để LLM sửa, không kèm DETAIL/traceback
    msg = getattr(getattr(e, "diag", None), "message_primary", None) or str(e)
    return msg.splitlines()[0][:300]


async def run_sql(question: str, ma_sv: str) -> dict:
    """Kết quả: {sql, columns, rows, row_count, empty, views, gia_dinh} hoặc {unsupported: lý do}.

    Lỗi sau khi hết lượt thử → raise RuntimeError (Executor ghi status=error).
    """
    allowed = set(view_columns())
    feedback = ""
    last_error = ""
    for attempt in range(MAX_RETRIES + 1):
        draft: SqlDraft = await _chain().ainvoke({
            "glossary": prompts.GLOSSARY, "schema": schema_context(), "question": question, "feedback": feedback,
        })
        if draft.khong_ho_tro:
            return {"unsupported": draft.khong_ho_tro, "gia_dinh": draft.gia_dinh}
        try:
            sql, views = check(draft.sql, allowed)
            columns, rows = await asyncio.to_thread(_execute, ma_sv, sql)
        except SqlRejected as e:
            last_error = str(e)
        except Exception as e:  # lỗi DB: cột sai, sai kiểu, timeout...
            last_error = _short_error(e)
            logger.warning("Text2SQL lần %d lỗi DB: %s | SQL: %s", attempt + 1, last_error, draft.sql)
        else:
            return {
                "sql": sql, "views": views, "columns": columns, "rows": rows,
                "row_count": len(rows), "empty": not rows, "gia_dinh": draft.gia_dinh,
            }
        feedback = prompts.FEEDBACK.format(sql=draft.sql, error=last_error)
    raise RuntimeError(f"Text2SQL thất bại sau {MAX_RETRIES + 1} lần: {last_error}")
