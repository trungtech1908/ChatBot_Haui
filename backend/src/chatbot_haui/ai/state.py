from typing import Optional, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    new_query: Optional[str]
    category: Optional[list[str]]
    retriever: Optional[list[str]]
    answer: Optional[str]
