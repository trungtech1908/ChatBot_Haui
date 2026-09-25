"""Kiểm tra SQL do LLM sinh trước khi chạy (ARCHITECTURE mục 2.7).

Parse bằng sqlglot, không dùng regex. Câu đem chạy là câu SINH LẠI từ cây cú pháp đã kiểm tra,
không phải chuỗi gốc của LLM, để tránh trường hợp parser hiểu một kiểu còn PostgreSQL chạy kiểu khác.

Đây chỉ là một lớp; các lớp còn lại: role chatbot_reader chỉ SELECT được schema chatbot, transaction
READ ONLY, statement_timeout, và view v_* tự lọc theo app.ma_sv.
"""
import sqlglot
from sqlglot import exp

MAX_ROWS = 50

# Hàm cấm: đổi/đọc phiên (set_config), làm treo (pg_sleep), đọc file / đối tượng hệ thống, kết nối ra ngoài
_FORBIDDEN_FUNCS = {
    "set_config", "current_setting", "query_to_xml", "query_to_xml_and_xmlschema", "table_to_xml",
    "cursor_to_xml", "database_to_xml", "schema_to_xml", "nextval", "setval", "currval", "txid_current",
    "version", "current_user", "session_user", "user", "inet_server_addr", "inet_client_addr",
}
_FORBIDDEN_PREFIXES = ("pg_", "lo_", "dblink", "file_")
# Nút không được xuất hiện ở bất kỳ đâu trong cây (kể cả trong CTE: WITH x AS (DELETE ...))
_FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Drop, exp.Alter, exp.TruncateTable,
    exp.Command, exp.Set, exp.Lock, exp.Into, exp.Copy, exp.Grant, exp.Transaction, exp.Commit, exp.Rollback,
)
_QUERY_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)


class SqlRejected(ValueError):
    """Lý do từ chối — được đưa lại cho LLM để sinh lại, không trả cho người dùng."""


def _func_name(func: exp.Func) -> str:
    return (func.name if isinstance(func, exp.Anonymous) else func.sql_name()).lower()


def check(sql: str, allowed_views: set[str]) -> tuple[str, list[str]]:
    """Trả về (SQL đã chuẩn hóa để chạy, danh sách view được dùng). Không hợp lệ → SqlRejected."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except sqlglot.errors.SqlglotError as e:
        raise SqlRejected(f"SQL không hợp lệ: {str(e).splitlines()[0]}") from e
    if len(statements) != 1:
        raise SqlRejected("Chỉ được đúng một câu lệnh")
    tree = statements[0]
    if not isinstance(tree, _QUERY_ROOTS):
        raise SqlRejected("Câu lệnh phải là SELECT (được dùng WITH)")

    for node_type in _FORBIDDEN_NODES:
        if tree.find(node_type):
            raise SqlRejected(f"Không được dùng {node_type.__name__.upper()}")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    used = set()
    for table in tree.find_all(exp.Table):
        name, schema = table.name.lower(), table.db.lower()
        if not name:
            raise SqlRejected("Không được đọc từ hàm trả bảng")
        if not schema and name in cte_names:
            continue
        if table.catalog or schema != "chatbot" or name not in allowed_views:
            raise SqlRejected(f"Chỉ được dùng các view trong schema chatbot, không được dùng {table.sql(dialect='postgres')}")
        used.add(name)
    if not used:
        raise SqlRejected("Câu lệnh phải đọc từ ít nhất một view của schema chatbot")

    for func in tree.find_all(exp.Func):
        name = _func_name(func)
        if name in _FORBIDDEN_FUNCS or name.startswith(_FORBIDDEN_PREFIXES):
            raise SqlRejected(f"Không được gọi hàm {name}")

    # LIMIT ≤ MAX_ROWS ở câu ngoài cùng; thiếu hoặc lớn hơn thì đặt lại
    limit = tree.args.get("limit")
    value = limit.expression if isinstance(limit, exp.Limit) else None
    if not (isinstance(value, exp.Literal) and value.is_int and int(value.this) <= MAX_ROWS):
        tree.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))

    return tree.sql(dialect="postgres", comments=False), sorted(used)
