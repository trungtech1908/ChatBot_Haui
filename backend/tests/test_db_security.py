"""Lớp bảo vệ ở DB (ARCHITECTURE mục 6): phạm vi dòng theo app.ma_sv, quyền của role chatbot, READ ONLY."""
import pytest
from sqlalchemy import text

from chatbot_haui.ai.tools import text2sql
from chatbot_haui.db.session import chatbot_engine, chatbot_scope

A, B = "2024619567", "2023654041"


def _one(ma_sv, sql):
    with chatbot_scope(ma_sv) as conn:
        return conn.execute(text(sql)).scalar()


def test_views_only_show_logged_in_student(database):
    assert _one(A, "SELECT ma_sv FROM chatbot.v_sinh_vien") == A
    assert _one(B, "SELECT ma_sv FROM chatbot.v_sinh_vien") == B
    assert _one(A, "SELECT count(DISTINCT ma_hk) FROM chatbot.v_diem") > 0


def test_views_empty_without_scope(database):
    with chatbot_engine().connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM chatbot.v_diem")).scalar() == 0


@pytest.mark.parametrize("sql", [
    "SELECT count(*) FROM core.sinh_vien",
    "SELECT count(*) FROM private.tai_khoan",
    "SELECT count(*) FROM public.chat_message",
])
def test_chatbot_role_cannot_read_outside_views(database, sql):
    with pytest.raises(Exception, match="permission denied"):
        _one(A, sql)


def test_scope_transaction_is_read_only(database):
    with pytest.raises(Exception, match="read-only transaction"):
        _one(A, "SELECT set_config('app.ma_sv', 'x', false); CREATE TEMP TABLE t (a int)")


def test_text2sql_hides_identity_columns(database):
    columns, rows = text2sql._execute(A, "SELECT ma_sv, ho_ten, nganh FROM chatbot.v_sinh_vien LIMIT 1")
    assert columns == ["nganh"] and rows == [{"nganh": "Công nghệ thông tin"}]


def test_text2sql_literal_with_colon_and_percent(database):
    # Chạy qua cursor driver: ':abc' / '%' trong literal không bị hiểu nhầm là tham số
    columns, rows = text2sql._execute(A, "SELECT count(*) AS n FROM chatbot.v_diem WHERE mon ILIKE '%:x%'")
    assert rows == [{"n": 0}]


def test_all_views_described_in_prompt(database):
    assert set(text2sql.view_columns()) == set(text2sql.prompts.VIEW_DOCS)
