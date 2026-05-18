import os
from typing import List, Optional, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "RAG_Chatbot_HaUI")
ENABLE_EXTERNAL_RERANK = os.getenv("ENABLE_EXTERNAL_RERANK", "").lower() in ("1", "true", "yes")
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "3"))

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
llm = ChatGroq(model="openai/gpt-oss-120b", api_key=GROQ_API_KEY)
llm_fast = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)


class AgentState(TypedDict, total=False):
    query: str
    new_query: Optional[str]
    needs_retrieval: Optional[bool]
    needs_db: Optional[bool]
    category: Optional[List[str]]
    retriever: Optional[List[str]]
    db_context: Optional[str]
    zep_context: Optional[str]
    answer: Optional[str]
    quality_ok: Optional[bool]
    quality_feedback: Optional[str]
    iteration: int
    max_iterations: int
    ma_sv: Optional[str]
    user_id: Optional[str]
    thread_id: Optional[str]
    ho_ten: Optional[str]
    chat_history: Optional[List[dict]]
