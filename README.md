# Chatbot HaUI — Agentic RAG

Chatbot hỏi đáp quy chế/quy định sinh viên: Vector DB (Qdrant) + truy vấn CSDL cá nhân + bộ nhớ Zep.

## Cấu trúc thư mục

```
Chatbot_Haui/
├── src/chatbot_haui/          # Mã ứng dụng chính (package Python)
│   ├── agent/                 # LangGraph + các agent node
│   │   ├── graph.py
│   │   ├── state.py           # LLM, Qdrant, AgentState
│   │   └── nodes/             # rewrite, retriever, quality, ...
│   ├── auth/                  # Đăng nhập → StudentSession (maSV)
│   ├── db/                    # ORM, engine, truy vấn SQL an toàn
│   ├── memory/                # Zep Cloud
│   ├── knowledge/             # Mô tả schema DB & nguồn quy chế
│   ├── cli.py                 # Entry CLI
│   └── paths.py
├── pipelines/                 # Offline: chunking, ingest Qdrant
├── scripts/                   # Tiện ích vận hành (Qdrant index)
├── sql/                       # Script MySQL (view bảo mật agent)
├── tests/
├── main.py                    # Wrapper → chatbot_haui.cli
├── pyproject.toml
├── requirements.txt
└── requirements-rag.txt
```

## Cài đặt

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
pip install -e .                    # cài package chatbot_haui
pip install -r requirements-rag.txt # BGE embedding (tuỳ chọn)
cp .env.example .env                # điền API keys
```

## Chạy

```bash
# Đăng nhập (maSV từ tài khoản, không từ .env)
python -m chatbot_haui

# Một câu hỏi
python -m chatbot_haui "Tôi có nhận được học bổng không"

# Dev: bỏ login
python -m chatbot_haui --ma-sv SV001 -q "..."
```

## MySQL agent

Chạy `sql/agent_secure_views.sql`, tạo user `agent_runtime`. Mỗi request set `@current_maSV` từ phiên đăng nhập.

## LangSmith

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=...
export LANGCHAIN_PROJECT=haui-chatbot
```
