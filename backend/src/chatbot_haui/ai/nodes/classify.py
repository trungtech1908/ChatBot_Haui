from langchain_core.output_parsers import CommaSeparatedListOutputParser
from langchain_core.prompts import ChatPromptTemplate

from chatbot_haui.ai.llm import get_llm
from chatbot_haui.ai.prompts import classify as prompts
from chatbot_haui.ai.state import AgentState

chain = (
    ChatPromptTemplate.from_messages([("system", prompts.SYSTEM_PROMPT), ("human", prompts.HUMAN_PROMPT)])
    | get_llm()
    | CommaSeparatedListOutputParser()
)


def classify(state: AgentState) -> dict:
    category = chain.invoke({
        "description": prompts.DOCUMENT_DESCRIPTIONS,
        "examples": prompts.FEW_SHOT_EXAMPLES,
        "user_query": state["query"],
    })
    return {"category": category}
