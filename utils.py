import re
from config import MAX_TOKENS, MIN_TOKENS, OVERLAP

def tokens(text: str) -> int:
    """Estimate token count (1 token ≈ 4 characters)"""
    return len(text) // 4

def chunk_text(text: str) -> list[dict]:
    # Split by sentence boundaries
    sents = re.split(r'(?<=[.!?])\s+', text)
    chunks, cur, cur_t = [], [], 0

    for s in sents:
        s = s.strip()
        if not s:
            continue
            
        t = tokens(s)
        
        # If adding this sentence exceeds max tokens, save current chunk
        if cur_t + t > MAX_TOKENS and cur:
            txt = ' '.join(cur)
            if tokens(txt) >= MIN_TOKENS:
                chunks.append({"text": txt, "tokens": cur_t})
            
            # Keep overlap sentences for context
            overlap = cur[-OVERLAP:] if len(cur) > OVERLAP else cur
            cur = overlap + [s]
            cur_t = sum(tokens(x) for x in overlap) + t
        else:
            cur.append(s)
            cur_t += t
    
    # Add remaining sentences
    if cur:
        txt = ' '.join(cur)
        if tokens(txt) >= MIN_TOKENS:
            chunks.append({"text": txt, "tokens": cur_t})
    
    return chunks

def bm25_score(text: str, query: str) -> float:
    t, q = text.lower(), query.lower().split()
    return sum(t.count(w) / (1 + len(t.split())) for w in q)