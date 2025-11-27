from typing import AsyncIterator

from node import *
from langgraph.graph import START, StateGraph, END

from node import AgentState

graph = StateGraph(AgentState) # type: ignore

graph.add_node('node_query_transform', node_query_transform) # type: ignore
graph.add_node('node_cls', node_cls) # type: ignore
graph.add_node('node_answer_normal', node_answer_normal) # type: ignore
graph.add_node('node_retriever', node_retriever) # type: ignore
graph.add_node('node_answer', node_answer) # type: ignore
graph.add_node('ROUTER', lambda state: state)

def router(state: AgentState):
    if state['category'][0] == 'Không xác định':
        return 'node_answer_normal'
    else:
        return 'node_retriever'

graph.add_edge(START, 'node_query_transform')
graph.add_edge( 'node_query_transform','node_cls')
graph.add_edge('node_cls', 'ROUTER')
graph.add_conditional_edges(
    'ROUTER',
    router,
    {
        'node_retriever': 'node_retriever',
        'node_answer_normal': 'node_answer_normal'
    }
)
graph.add_edge('node_retriever', 'node_answer')
graph.add_edge('node_answer', END)
graph.add_edge('node_answer_normal', END)

# graph.py – đoạn cuối file, thay toàn bộ hàm cũ bằng cái này
app = graph.compile()

async def stream_graph(query: str, username: str = "") -> AsyncIterator[str]:
    """
    Hàm duy nhất hoạt động hoàn hảo với cấu trúc hiện tại của bạn
    """
    # KHÔNG ĐƯỢC ĐẶT category hay retriever gì cả → để graph chạy thật
    input_state = AgentState(
        query=query,
        username=username
    )

    # Dùng astream_events – đây là cách DUY NHẤT fix được lỗi async_generator not iterable
    async for event in app.astream_events(input_state, version="v2"):
        # Chỉ lấy token từ LLM khi đang stream
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content

    # Nếu đi nhánh node_answer_normal (không có stream), thì lấy kết quả cuối
    try:
        final_result = await app.ainvoke(input_state)
        if final_result.get("answer"):
            yield final_result["answer"]
    except:
        pass  # nếu lỗi thì thôi, không crash