from langchain_google_genai import GoogleGenerativeAIEmbeddings
from typing import List

_model = None

def get_model():
    """Initialize and return the embedding model (singleton)"""
    global _model
    if _model is None:
        print("🔧 Loading Gemini embedding model...")
        _model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")
        print("✅ Model loaded")
    return _model

def generate_embedding(text: str) -> List[float]:
    """Generate embedding for single text"""
    model = get_model()
    embedding = model.embed_query(text)
    return embedding


def generate_many_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts (batch)"""
    model = get_model()
    embeddings = model.embed_documents(texts)
    return embeddings