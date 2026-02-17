import cohere
from typing import List
import time
from app.config import settings

_cohere_client = None

def get_cohere_client():
    """Initialize Cohere client (singleton)"""
    global _cohere_client
    if _cohere_client is None:
        print("🔧 Initializing Cohere client...")
        _cohere_client = cohere.Client(settings.COHERE_API_KEY)
        print("✅ Cohere client ready")
    return _cohere_client

def generate_embedding(text: str) -> List[float]:
    """
    Generate single embedding using Cohere API.
    Returns 1024-dimensional vector.
    """
    client = get_cohere_client()
    response = client.embed(
        texts=[text],
        model="embed-english-v3.0",
        input_type="search_document"
    )
    return response.embeddings[0]

def generate_many_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate batch embeddings using Cohere API.
    Processes up to 96 texts per request (Cohere's limit).
    """
    if not texts:
        return []
    
    client = get_cohere_client()
    start_time = time.time()
    
    print(f"🧮 Generating {len(texts)} embeddings with Cohere API...")
    
    # Process in batches of 96
    batch_size = 96
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            response = client.embed(
                texts=batch,
                model="embed-english-v3.0",
                input_type="search_document"
            )
            all_embeddings.extend(response.embeddings)
            
            batch_num = i // batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            print(f"  ✅ Batch {batch_num}/{total_batches}: {len(batch)} embeddings generated")
            
        except Exception as e:
            print(f"❌ Error in batch {i//batch_size + 1}: {str(e)}")
            raise
    
    elapsed = time.time() - start_time
    rate = len(texts) / elapsed if elapsed > 0 else 0
    print(f"✅ Generated {len(texts)} embeddings in {elapsed:.2f}s ({rate:.1f} emb/sec)")
    
    return all_embeddings


# from sentence_transformers import SentenceTransformer
# import time
# from typing import List

# _model = None

# def get_model():
#     """Initialize and return the embedding model (singleton)"""
#     global _model
#     if _model is None:
#         start_time = time.time()
#         print("🔧 Loading SentenceTransformer model...")
#         _model = SentenceTransformer("all-MiniLM-L6-v2")
#         print(f"✅ Model loaded in {time.time() - start_time} seconds")
#     return _model

# # def generate_embedding(text: str) -> List[float]:
# #     """Generate embedding for single text"""
# #     model = get_model()
# #     embedding = model.embed_query(text)
# #     return embedding
# def generate_embedding(text: str) -> List[float]:
#     """Generate embedding for single text"""
#     model = get_model()
#     embedding = model.encode(text,convert_to_tensor=False)
#     return embedding.tolist()  # Convert to list for JSON serialization


# # def generate_many_embeddings(texts: List[str]) -> List[List[float]]:
# #     """Generate embeddings for multiple texts (batch)"""
# #     model = get_model()
# #     embeddings = model.embed_documents(texts)
# #     return embeddings

# def generate_many_embeddings(texts: List[str]) -> List[List[float]]:
#     """Generate embeddings for multiple texts (batch)"""
#     model = get_model()
#     start_time = time.time()
#     embeddings = model.encode(texts,convert_to_tensor=False,batch_size=32)
#     print(f"✅ Generated embeddings for {len(texts)} texts in {time.time() - start_time} seconds")
#     return [emb.tolist() for emb in embeddings]