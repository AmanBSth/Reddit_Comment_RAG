import json
import praw
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
from config import (
    OPENAI_API_KEY, OPENROUTER_API_KEY, LLM_MODEL, EMBEDDING_MODEL,
    FALLBACK_EMBEDDING_MODEL, VECTOR_DB_DISTANCE, REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT, K, TOP_K
)
from utils import bm25_score

# === REDDIT SCRAPER ===

def get_reddit_client():
    """Initialize and return Reddit API client"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        raise ValueError("Reddit API credentials not found in environment variables")
    
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

def scrape_reddit(topic: str, limit: int = 100, comments_per_post: int = 30) -> str:
    reddit = get_reddit_client()
    comments = []
    
    try:
        # Search across all subreddits
        for post in reddit.subreddit("all").search(topic, limit=limit, sort="relevance"):
            # Add post content if available
            if post.selftext and post.selftext not in ["[deleted]", "[removed]"]:
                comments.append(f"POST: {post.title}\n{post.selftext}")
            
            # Add comments from the post
            try:
                post.comments.replace_more(limit=0)
                for comment in post.comments.list()[:comments_per_post]:
                    if (hasattr(comment, 'author') and 
                        comment.author and 
                        hasattr(comment, 'body') and 
                        comment.body not in ["[deleted]", "[removed]"]):
                        comments.append(comment.body.strip())
            except Exception as e:
                # Skip posts with comment retrieval errors
                continue
                
    except Exception as e:
        raise Exception(f"Error scraping Reddit: {e}")
    
    return "\n\n".join(comments)


# === VECTOR DATABASE ===

class VectorDB:
    """Vector database for storing and retrieving document chunks"""
    
    def __init__(self, name: str = "reddit_rag"):

        self.client = chromadb.Client()
        
        # Use OpenAI embeddings if available, otherwise fall back to local model
        if OPENAI_API_KEY:
            ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name=EMBEDDING_MODEL
            )
        else:
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=FALLBACK_EMBEDDING_MODEL
            )
        
        # Get or create collection
        try:
            self.coll = self.client.get_collection(name, embedding_function=ef)
        except:
            self.coll = self.client.create_collection(
                name,
                embedding_function=ef,
                metadata={"hnsw:space": VECTOR_DB_DISTANCE}
            )
    
    def add(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        
        self.coll.add(
            documents=[c["text"] for c in chunks],
            ids=[f"c{i}" for i in range(len(chunks))],
            metadatas=[{"tokens": c["tokens"]} for c in chunks]
        )
    
    def search(self, query: str, k: int = 10) -> list[dict]:
        """
        Search for relevant chunks
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of dicts with 'text', 'score', and 'metadata' keys
        """
        results = self.coll.query(query_texts=[query], n_results=k)
        
        return [
            {
                "text": doc,
                "score": 1 - dist,
                "metadata": meta
            }
            for doc, dist, meta in zip(
                results["documents"][0],
                results["distances"][0],
                results["metadatas"][0]
            )
        ]
    
    def clear(self) -> None:
        """Clear all data from the collection"""
        try:
            self.client.delete_collection(self.coll.name)
        except:
            pass
        self.__init__(self.coll.name)


# === RETRIEVAL & RERANKING ===

# Initialize LLM client
llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
) if OPENROUTER_API_KEY else None

def hybrid_search(db, query: str, k: int = K, alpha: float = 0.7) -> list[dict]:
    # Get initial results from vector database
    results = db.search(query, k * 2)
    
    # Calculate hybrid scores
    for r in results:
        r["hybrid"] = alpha * r["score"] + (1 - alpha) * bm25_score(r["text"], query)
    
    # Sort by hybrid score and return top k
    return sorted(results, key=lambda x: x["hybrid"], reverse=True)[:k]

def rerank_llm(query: str, candidates: list[dict], k: int = TOP_K) -> list[dict]:
    """
    Use LLM to rerank candidates by relevance
    
    Args:
        query: Search query
        candidates: List of candidate documents
        k: Number of top results to return
        
    Returns:
        Reranked list of documents
    """
    if not llm:
        return candidates[:k]
    
    # Create ranking prompt
    prompt = (
        f"Rank by relevance to: \"{query}\"\n"
        f"Return ONLY JSON array of indices [2,0,...]\n\n"
    )
    prompt += "\n\n".join(
        f"[{i}] {c['text'][:300]}..."
        for i, c in enumerate(candidates[:20])
    )
    
    try:
        # Get LLM ranking
        response = llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0
        )
        
        resp_text = response.choices[0].message.content.strip()
        
        # Clean up response (remove markdown code blocks if present)
        if resp_text.startswith("```"):
            resp_text = resp_text.split("```")[1].replace("json", "").strip()
        
        # Parse indices and reorder candidates
        indices = json.loads(resp_text)[:k]
        return [candidates[i] for i in indices if i < len(candidates)]
        
    except Exception as e:
        # Fall back to original order on error
        print(f"Reranking error: {e}")
        return candidates[:k]