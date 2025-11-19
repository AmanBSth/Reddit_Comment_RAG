import os
from dotenv import load_dotenv

load_dotenv()

MAX_TOKENS = 512
MIN_TOKENS = 100
OVERLAP = 2
K = 20
TOP_K = 5

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit_rag_app/1.0")

LLM_MODEL = "openai/gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
FALLBACK_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

VECTOR_DB_NAME = "reddit_rag"
VECTOR_DB_DISTANCE = "cosine"