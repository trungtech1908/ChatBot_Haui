import asyncio
from time import time
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


async def main():
    start = time()
    input_state = AgentState(query='Tôi bị bắt phao thì có làm sao không')
    app = graph.compile()

    res = AgentState(**await app.ainvoke(input_state)) # type: ignore
    end = time()
    print('\n\n',end-start)
    print('\n\n',res['new_query'])
    print(res['category'])

asyncio.run(main())



