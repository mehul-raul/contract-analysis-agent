from sentence_transformers import SentenceTransformer
import time
from typing import List

_model = None

def get_model():
    """Initialize and return the embedding model (singleton)"""
    global _model
    if _model is None:
        start_time = time.time()
        print("🔧 Loading SentenceTransformer model...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print(f"✅ Model loaded in {time.time() - start_time} seconds")
    return _model

# def generate_embedding(text: str) -> List[float]:
#     """Generate embedding for single text"""
#     model = get_model()
#     embedding = model.embed_query(text)
#     return embedding
def generate_embedding(text: str) -> List[float]:
    """Generate embedding for single text"""
    model = get_model()
    embedding = model.encode(text,convert_to_tensor=False)
    return embedding.tolist()  # Convert to list for JSON serialization


# def generate_many_embeddings(texts: List[str]) -> List[List[float]]:
#     """Generate embeddings for multiple texts (batch)"""
#     model = get_model()
#     embeddings = model.embed_documents(texts)
#     return embeddings

def generate_many_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts (batch)"""
    model = get_model()
    start_time = time.time()
    embeddings = model.encode(texts,convert_to_tensor=False,batch_size=32)
    print(f"✅ Generated embeddings for {len(texts)} texts in {time.time() - start_time} seconds")
    return [emb.tolist() for emb in embeddings]