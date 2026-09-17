from collections.abc import AsyncIterator
from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from chatbot_haui.ai.prompts.classify import UNKNOWN
from chatbot_haui.ai.state import AgentState

ANSWER_NODES = {"answer", "answer_general"}


def route(state: AgentState) -> str:
    return "answer_general" if not state["category"] or state["category"][0] == UNKNOWN else "retrieve"


@lru_cache
def get_graph() -> CompiledStateGraph:
    """Dựng graph lần đầu được gọi (nạp LLM, model embedding, client Qdrant)."""
    from chatbot_haui.ai.nodes import answer, answer_general, classify, query_transform, retrieve

    builder = StateGraph(AgentState)
    builder.add_node("query_transform", query_transform)
    builder.add_node("classify", classify)
    builder.add_node("retrieve", retrieve)
    builder.add_node("answer", answer)
    builder.add_node("answer_general", answer_general)

    builder.add_edge(START, "query_transform")
    builder.add_edge("query_transform", "classify")
    builder.add_conditional_edges("classify", route, ["retrieve", "answer_general"])
    builder.add_edge("retrieve", "answer")
    builder.add_edge("answer", END)
    builder.add_edge("answer_general", END)
    return builder.compile()


async def run(query: str) -> AgentState:
    return await get_graph().ainvoke({"query": query})


async def stream(query: str) -> AsyncIterator[str]:
    # Chỉ stream token của node trả lời, bỏ token của query_transform/classify
    async for event in get_graph().astream_events({"query": query}, version="v2"):
        if event["event"] == "on_chat_model_stream" and event["metadata"].get("langgraph_node") in ANSWER_NODES:
            if content := event["data"]["chunk"].content:
                yield content
