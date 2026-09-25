"""Lớp kiểm tra SQL (ai/tools/sql_guard.py): câu hợp lệ phải qua và được giới hạn LIMIT; mọi dạng vượt phạm vi bị chặn."""
import pytest

from chatbot_haui.ai.tools.sql_guard import MAX_ROWS, SqlRejected, check

VIEWS = {"v_diem", "v_ket_qua_hk", "v_sinh_vien", "ref_muc_tran", "v_cong_no"}


@pytest.mark.parametrize("sql", [
    "SELECT hoc_ky, tb_tich_luy FROM chatbot.v_ket_qua_hk ORDER BY ma_hk DESC LIMIT 1",
    "WITH x AS (SELECT ma_hk, con_no FROM chatbot.v_cong_no) SELECT ma_hk FROM x WHERE con_no > 0",
    "SELECT m.muc_thang FROM chatbot.ref_muc_tran m JOIN chatbot.v_sinh_vien s ON s.ma_khoi = m.ma_khoi",
    "SELECT mon FROM chatbot.v_diem UNION SELECT hoc_ky FROM chatbot.v_ket_qua_hk",
    "SELECT SUM(so_tc) FILTER (WHERE dat) AS tc, LEFT(ma_hk, 4)::int AS y FROM chatbot.v_diem GROUP BY 2",
    "SELECT mon FROM chatbot.v_diem WHERE mon ILIKE '%lập trình:c%'",
])
def test_valid_queries_pass(sql):
    out, used = check(sql, VIEWS)
    assert used and f"LIMIT {MAX_ROWS}" in out or "LIMIT 1" in out


@pytest.mark.parametrize("sql, expected_limit", [
    ("SELECT mon FROM chatbot.v_diem", MAX_ROWS),          # thiếu → thêm
    ("SELECT mon FROM chatbot.v_diem LIMIT 1000", MAX_ROWS),  # quá lớn → hạ
    ("SELECT mon FROM chatbot.v_diem LIMIT 3", 3),          # hợp lệ → giữ
])
def test_limit_is_enforced(sql, expected_limit):
    out, _ = check(sql, VIEWS)
    assert out.endswith(f"LIMIT {expected_limit}")


@pytest.mark.parametrize("sql", [
    # ra ngoài schema chatbot
    "SELECT * FROM core.sinh_vien",
    "SELECT * FROM sinh_vien",
    "SELECT * FROM private.tai_khoan",
    "SELECT * FROM pg_catalog.pg_roles",
    "SELECT * FROM information_schema.tables",
    "SELECT mon FROM chatbot.v_diem WHERE EXISTS (SELECT 1 FROM core.sinh_vien)",
    "SELECT * FROM chatbot.v_khong_co",
    # đổi phạm vi / hàm nguy hiểm
    "SELECT set_config('app.ma_sv', '2024000000', true), mon FROM chatbot.v_diem",
    "SELECT current_setting('app.ma_sv') FROM chatbot.v_diem",
    "SELECT pg_sleep(10) FROM chatbot.v_diem",
    "SELECT pg_read_file('/etc/passwd') FROM chatbot.v_diem",
    "SELECT dblink('host=x', 'select 1') FROM chatbot.v_diem",
    "SELECT * FROM generate_series(1, 100000000)",
    # ghi / nhiều lệnh / khóa
    "SELECT 1 FROM chatbot.v_diem; DROP TABLE core.sinh_vien",
    "DELETE FROM chatbot.v_diem",
    "WITH d AS (DELETE FROM core.diem_hp RETURNING *) SELECT mon FROM chatbot.v_diem",
    "SET app.ma_sv = '2024000000'",
    "SELECT mon FROM chatbot.v_diem FOR UPDATE",
    "SELECT mon INTO core.x FROM chatbot.v_diem",
    # không phải truy vấn dữ liệu
    "UNSUPPORTED",
    "SELECT 1",
    "",
])
def test_out_of_scope_queries_rejected(sql):
    with pytest.raises(SqlRejected):
        check(sql, VIEWS)


def test_executed_sql_is_regenerated_from_tree():
    # Chú thích (có thể giấu nội dung) bị bỏ: câu chạy là câu sinh lại từ cây đã kiểm tra
    out, _ = check("SELECT mon /* set_config('app.ma_sv','x',true) */ FROM chatbot.v_diem", VIEWS)
    assert "set_config" not in out and "/*" not in out
