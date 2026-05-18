import json
import ollama
import re

# Load schema
from chatbot_haui.paths import KNOWLEDGE_DIR

with open(KNOWLEDGE_DIR / "describe_DB.json", encoding="utf-8") as f:
    schema = json.load(f)

schema_text = json.dumps(schema, ensure_ascii=False)

# Text tự nhiên
user_text = """
Liệt kê giảng viên dạy các môn học có học kỳ >= 3
"""

# Prompt
prompt = f"""
TASK:
Convert the user request into EXACTLY ONE SQL query.

RULES (ABSOLUTE):
- SQL dialect: MySQL 8.0 ONLY
- Use ONLY tables and columns from the schema
- Table and column names are CASE-SENSITIVE
- DO NOT invent tables or columns
- DO NOT output more than ONE SQL query
- DO NOT use Oracle / PostgreSQL functions
- NO explanation, NO comments, NO markdown

DATABASE SCHEMA:
{schema_text}

USER REQUEST:
{user_text}

SQL:
"""

# Gọi SQLCoder (KHÔNG num_ctx)
result = ollama.generate(
    model="sqlcoder:7b",
    prompt=prompt,
    options={
        "temperature": 0.0,
        "top_p": 1.0,
        "stop": ["\n\n", "<s>", "</s>"]
    }
)

raw_output = result["response"]

# Lấy đúng 1 câu SQL
match = re.search(r"(SELECT[\s\S]+?;)", raw_output, re.IGNORECASE)
if not match:
    raise RuntimeError("Model không sinh ra SQL hợp lệ")

sql = match.group(1)
print(sql)
