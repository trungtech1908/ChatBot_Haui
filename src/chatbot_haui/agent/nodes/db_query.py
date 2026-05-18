from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.db.agent_query import generate_and_run_sql
from chatbot_haui.agent.state import AgentState, llm_fast
from chatbot_haui.agent.nodes.parsers import parse_json_object

DB_DECIDE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """Quyết định có cần truy vấn CSDL sinh viên (GPA, đối tượng, nợ HP...) không.
JSON: {{"needs_db": true/false, "reason": "..."}}
needs_db=true khi câu hỏi cá nhân (tôi/em) VÀ cần số liệu thực tế để trả lời (đủ điều kiện học bổng, đã qua môn, nợ bao nhiêu...)."""),
    ("human", """Câu hỏi: {question}
Ngữ cảnh quy chế đã retrieve:
{rag_context}"""),
])


def node_db_decide(state: AgentState) -> AgentState:
    if state.get("needs_db") is False and not state.get("needs_retrieval"):
        return state

    rag_snippet = "\n".join((state.get("retriever") or [])[:3])[:2000]
    chain = DB_DECIDE_PROMPT | llm_fast | StrOutputParser()
    raw = chain.invoke({
        "question": state.get("new_query") or state["query"],
        "rag_context": rag_snippet or "(chưa có)",
    })
    parsed = parse_json_object(raw)
    if "needs_db" in parsed:
        state["needs_db"] = bool(parsed["needs_db"])
    return state


def node_db_query(state: AgentState) -> AgentState:
    if not state.get("needs_db"):
        state["db_context"] = ""
        return state

    ma_sv = state.get("ma_sv")
    if not ma_sv:
        state["db_context"] = "Chưa có phiên sinh viên — không tra cứu được dữ liệu cá nhân."
        return state

    rag_hint = "\n".join(state.get("retriever") or [])[:2500]
    ok, result = generate_and_run_sql(
        llm_fast,
        ma_sv,
        state.get("new_query") or state["query"],
        rag_hint=rag_hint,
    )
    state["db_context"] = result if ok else f"(Không truy vấn được CSDL: {result})"
    return state
