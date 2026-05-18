"""Truy vấn MySQL an toàn cho Agent — chỉ SELECT trên view/bảng được phép."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Optional

import mysql.connector
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

from chatbot_haui.paths import KNOWLEDGE_DIR

SCHEMA_PATH = KNOWLEDGE_DIR / "describe_DB.json"

ALLOWED_RELATIONS = frozenset({
    "v_sinhVien", "v_taiChinh", "v_doiTuong", "v_dieuKienTotNghiep",
    "v_ketQuaMonHoc", "v_giaoDich", "v_sinhVienLopHoc", "v_lichThiSV", "v_thucTap",
    "monHoc", "lopHoc", "khoa", "giangVien", "ctdt", "nhomMH", "ct_nmh", "ct_ctdt",
})

FORBIDDEN_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bmatKhau\b", r"\btaiKhoan\b", r"\bpassword\b",
        r"\bINSERT\b", r"\bUPDATE\b", r"\bDELETE\b", r"\bDROP\b", r"\bALTER\b",
        r"\bTRUNCATE\b", r"\bGRANT\b", r"\bUNION\b", r"@current_maSV",
        r"\bsinhVien\b", r"\btaiChinh\b", r"\bdoiTuong\b",
        r"\bdieuKienTotNghiep\b", r"\bketQuaMonHoc\b", r"\bgiaoDich\b",
        r"\blichThiSV\b", r"\bthucTap\b", r"\bsinhVienLopHoc\b",
    ]
]

AGENT_DB_CONFIG = {
    "host": os.getenv("AGENT_DB_HOST", "localhost"),
    "user": os.getenv("AGENT_DB_USER", "agent_runtime"),
    "password": os.getenv("AGENT_DB_PASSWORD", "strong_pwd"),
    "database": os.getenv("AGENT_DB_NAME", "CSDLDoAnCN"),
    "port": int(os.getenv("AGENT_DB_PORT", "3306")),
}


def _load_schema_text() -> str:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    allowed = set(ALLOWED_RELATIONS)
    filtered_tables = [
        t for t in schema.get("tables", [])
        if t["table_name"] in allowed or t["table_name"].startswith("v_")
    ]
    view_schema = {
        "tables": filtered_tables,
        "relationships": schema.get("relationships", []),
        "note": (
            "Agent CHỈ được dùng các view v_* (đã lọc theo sinh viên hiện tại). "
            "KHÔNG dùng bảng gốc sinhVien, taiKhoan, matKhau. "
            "KHÔNG cần WHERE maSV — view đã lọc sẵn."
        ),
    }
    return json.dumps(view_schema, ensure_ascii=False, indent=2)


def validate_sql(sql: str) -> tuple[bool, str]:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        return False, "Câu SQL rỗng"
    if not re.match(r"^\s*SELECT\b", cleaned, re.IGNORECASE):
        return False, "Chỉ cho phép SELECT"
    if ";" in cleaned:
        return False, "Không cho phép nhiều câu lệnh"
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(cleaned):
            return False, f"SQL chứa pattern bị cấm: {pat.pattern}"
    from_tables = re.findall(r"\bFROM\s+([`']?)(\w+)\1", cleaned, re.IGNORECASE)
    join_tables = re.findall(r"\bJOIN\s+([`']?)(\w+)\1", cleaned, re.IGNORECASE)
    used = {t.lower() for _, t in from_tables + join_tables}
    for name in used:
        if name not in {r.lower() for r in ALLOWED_RELATIONS}:
            return False, f"Bảng không được phép: {name}"
    return True, cleaned + ";"


def execute_safe_query(ma_sv: str, sql: str) -> tuple[bool, str]:
    ok, result = validate_sql(sql)
    if not ok:
        return False, result

    conn = None
    try:
        conn = mysql.connector.connect(**AGENT_DB_CONFIG)
        cur = conn.cursor(dictionary=True)
        cur.execute("SET @current_maSV = %s", (ma_sv,))
        cur.execute(result)
        rows: list[dict[str, Any]] = cur.fetchall()
        cur.close()
        if not rows:
            return True, "Không có dữ liệu phù hợp trong CSDL."
        lines = []
        for row in rows[:20]:
            safe_row = {k: v for k, v in row.items() if k.lower() not in ("matkhau", "password")}
            lines.append(json.dumps(safe_row, ensure_ascii=False, default=str))
        return True, "\n".join(lines)
    except mysql.connector.Error as e:
        return False, f"Lỗi truy vấn CSDL: {e}"
    finally:
        if conn:
            conn.close()


SQL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Bạn sinh ĐÚNG MỘT câu SQL MySQL 8.0 SELECT.
- CHỈ dùng view v_* và bảng public: monHoc, lopHoc, khoa, giangVien, ctdt.
- KHÔNG dùng sinhVien, taiKhoan, matKhau hay bảng gốc chứa dữ liệu SV.
- View v_* đã lọc theo sinh viên — KHÔNG thêm WHERE maSV.
- Chỉ lấy cột cần thiết cho câu hỏi (GPA, đối tượng chính sách, nợ học phí...).
- Không giải thích, không markdown, chỉ SQL."""),
    ("human", """Schema (rút gọn):
{schema}

Câu hỏi sinh viên: {question}
Ngữ cảnh quy chế (nếu có): {rag_hint}

SQL:"""),
])


def generate_and_run_sql(
    llm,
    ma_sv: str,
    question: str,
    rag_hint: str = "",
) -> tuple[bool, str]:
    model = llm
    if model is None:
        from chatbot_haui.agent.state import llm as default_llm
        model = default_llm
    chain = SQL_PROMPT | model | StrOutputParser()
    raw = chain.invoke({
        "schema": _load_schema_text(),
        "question": question,
        "rag_hint": rag_hint[:2000],
    })
    match = re.search(r"(SELECT[\s\S]+?;)", raw, re.IGNORECASE)
    if not match:
        return False, "Không sinh được SQL hợp lệ."
    return execute_safe_query(ma_sv, match.group(1))
