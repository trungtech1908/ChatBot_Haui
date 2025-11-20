import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from qdrant_client import QdrantClient

class AgentState(TypedDict, total=False):
    query: str
    new_query: Optional[str]
    category: Optional[list[str]]
    retriever: Optional[list[str]]
    answer: Optional[str]

load_dotenv()
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
QDRANT_URL = os.getenv('QDRANT_URL')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
llm_gemini = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=GOOGLE_API_KEY)
llm = ChatOllama(model='qwen2.5:7b', reasoning=False)
