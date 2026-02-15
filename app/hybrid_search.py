from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict
from app.embeddingmaker import generate_embedding
from sentence_transformers import CrossEncoder


def hybrid_search(db: Session,query: str,contract_id: int,top_k: int = 10) -> List[Dict]:
    """
    Hybrid search: Combine vector search + keyword search
    
    Steps:
    1. Vector search (semantic similarity)
    2. Keyword search (exact text matches)
    3. Combine using Reciprocal Rank Fusion (RRF)
    
    Returns:
        List of chunks with combined scores
    """
    
    # Step 1: Vector Search
    print("🔍 Running vector search...")
    query_embedding = generate_embedding(query)
    
    vector_sql = text("""
        SELECT 
            id,
            chunk_text,
            chunk_index,
            embedding <-> CAST(:query_embedding AS vector) AS distance
        FROM contract_chunks
        WHERE contract_id = :contract_id
        ORDER BY distance ASC
        LIMIT :limit
    """)
    
    vector_results = db.execute(
        vector_sql,
        {
            "query_embedding": str(query_embedding),
            "contract_id": contract_id,
            "limit": top_k
        }
    ).fetchall()
    
    # Step 2: Keyword Search (Full-Text Search)
    print("🔍 Running keyword search...")
    keyword_sql = text("""
        SELECT 
            id,
            chunk_text,
            chunk_index,
            ts_rank(
                to_tsvector('english', chunk_text),
                plainto_tsquery('english', :query)
            ) AS rank
        FROM contract_chunks
        WHERE contract_id = :contract_id
          AND to_tsvector('english', chunk_text) @@ plainto_tsquery('english', :query) 
        ORDER BY rank DESC
        LIMIT :limit
    """) #@@ means Does left match right?
    
    keyword_results = db.execute(
        keyword_sql,
        {
            "query": query,
            "contract_id": contract_id,
            "limit": top_k
        }
    ).fetchall()
    
    # Step 3: Reciprocal Rank Fusion (RRF)
    print("🔀 Combining results with RRF...")
    combined_scores = reciprocal_rank_fusion(vector_results, keyword_results)
    
    # Step 4: Get top K after fusion
    top_chunks = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # Step 5: Fetch full chunk details
    final_results = []
    for chunk_id, score in top_chunks:
        chunk = db.execute(
            text("SELECT id, chunk_text, chunk_index FROM contract_chunks WHERE id = :id"),
            {"id": chunk_id}
        ).fetchone()
        
        if chunk:
            final_results.append({
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.chunk_text,
                "hybrid_score": round(score, 3)
            })
    
    print(f"✅ Hybrid search found {len(final_results)} chunks")
    return final_results


def reciprocal_rank_fusion(
    vector_results: List,
    keyword_results: List,
    k: int = 60
) -> Dict[int, float]:
    """
    Combine rankings using Reciprocal Rank Fusion
    
    Formula: score = sum(1 / (k + rank))
    
    Args:
        vector_results: Results from vector search
        keyword_results: Results from keyword search
        k: Constant (default 60)
    
    Returns:
        Dict mapping chunk_id to combined score
    """
    scores = {}
    
    # Add vector search scores
    for rank, result in enumerate(vector_results):
        chunk_id = result.id
        score = 1 / (k + rank + 1)
        scores[chunk_id] = scores.get(chunk_id, 0) + score
    
    # Add keyword search scores
    for rank, result in enumerate(keyword_results):
        chunk_id = result.id
        score = 1 / (k + rank + 1)
        scores[chunk_id] = scores.get(chunk_id, 0) + score
    
    return scores



_reranker = None


def get_reranker():
    """Get or initialize reranker model"""
    global _reranker
    if _reranker is None:
        print("🔧 Loading reranker model...")
        _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        print("✅ Reranker loaded")
    return _reranker


def rerank_chunks(query: str, chunks: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Rerank chunks using cross-encoder
    
    Args:
        query: User question
        chunks: Candidate chunks from hybrid search
        top_k: How many to return after reranking
    
    Returns:
        Top K reranked chunks
    """
    if not chunks:
        return []
    
    print(f"🎯 Reranking {len(chunks)} chunks...")
    
    reranker = get_reranker()
    
   
    pairs = [(query, chunk['text']) for chunk in chunks]
    #above is same as pairs = []
    # for chunk in chunks:
    # pairs.append((query, chunk['text']))
    
    # Get reranking scores comapi to query
    scores = reranker.predict(pairs)
    
    # Add rerank scores to chunks
    for chunk, score in zip(chunks, scores):
        chunk['rerank_score'] = float(score) #here we make a rerank key in dict and assign the score to it
    
    # Sort by rerank score (higher = better)
    reranked = sorted(chunks, key=lambda x: x['rerank_score'], reverse=True)
    
    print(f"✅ Reranked, returning top {top_k}")
    
    return reranked[:top_k] #slicing done for top k out of 10