import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from qdrant_client import QdrantClient

from Valiadation_RAG.node.config import llm_gemini


class AgentState(TypedDict, total=False):
    query: str
    new_query: Optional[str]
    category: Optional[list[str]]
    retriever: Optional[list[str]]
    answer: Optional[str]
    username: Optional[str]

load_dotenv()
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# llm_gemini = ChatOllama(model='llama3.1:8b', reasoning=False)
# llm = ChatOllama(model='llama3.1:8b', reasoning=False)

llm_gemini = ChatGroq(model='openai/gpt-oss-120b', api_key=GROQ_API_KEY)
llm = ChatGroq(model='openai/gpt-oss-120b', api_key=GROQ_API_KEY)