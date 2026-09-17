from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.ai.llm import get_llm
from chatbot_haui.ai.prompts import query_transform as prompts
from chatbot_haui.ai.state import AgentState

chain = (
    ChatPromptTemplate.from_messages([("system", prompts.SYSTEM_PROMPT), ("human", prompts.HUMAN_PROMPT)])
    | get_llm()
    | StrOutputParser()
)


def query_transform(state: AgentState) -> dict:
    return {"new_query": chain.invoke({"user_query": state["query"]})}
