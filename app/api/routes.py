from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, Contract, ContractChunk, User
from app.pdf_read_chunk import extract_text_from_pdf, chunk_text
from app.embeddingmaker import generate_many_embeddings, generate_embedding
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Annotated
from app.auth import get_current_user 
from app.hybrid_search import hybrid_search, rerank_chunks

router = APIRouter()



@router.post("/upload")
def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)  # Now it's just an int
):
    """Upload a PDF contract (requires authentication)"""
    
    # Check if PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    try:
        # Extract text
        print(f"📄 Extracting text from {file.filename}...")
        full_text = extract_text_from_pdf(file.file)
        
        # Chunk text
        print("✂️ Chunking text...")
        chunks = chunk_text(full_text, chunk_size=500, overlap=50)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Generate embeddings
        print("🧮 Generating embeddings...")
        embeddings = generate_many_embeddings(chunks)
        print(f"✅ Generated {len(embeddings)} embeddings")
        
        # Save contract
        contract = Contract(
            user_id=user_id,  # Use the user_id from token
            filename=file.filename,
            num_chunks=len(chunks)
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        
        # Save chunks
        for idx, (chunk_text_val, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = ContractChunk(
                contract_id=contract.id,
                chunk_text=chunk_text_val,
                chunk_index=idx,
                embedding=embedding
            )
            db.add(chunk)
        
        db.commit()
        print(f"✅ Saved contract with ID: {contract.id} for user ID: {user_id}")
        
        return {
            "message": "Contract uploaded",
            "contract_id": contract.id,
            "filename": file.filename,
            "num_chunks": len(chunks),
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
class QueryRequest(BaseModel):
    contract_id: Annotated[int, Field(..., description="ID of the contract to query")]
    question: Annotated[str, Field(..., description="The question to ask about the contract")]
    top_k: Annotated[int, Field(5, description="Number of top similar chunks to retrieve")] = 5

@router.post("/query")
def query_contract(
    request: QueryRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Search contract using HYBRID search + RERANKING
    """
    
    # Step 0: Verify ownership
    contract = db.query(Contract).filter(
        Contract.id == request.contract_id,
        Contract.user_id == user_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found or you don't have access to it"
        )
    
    # Step 1: Hybrid search (get 10 candidates)
    print(f"🔍 User {user_id} searching contract {request.contract_id}: {request.question}")
    
    candidates = hybrid_search(
        db=db,
        query=request.question,
        contract_id=request.contract_id,
        top_k=10  # Get 10 candidates for reranking
    )
    
    if not candidates:
        raise HTTPException(status_code=404, detail="No relevant chunks found")
    
    # Step 2: Rerank to get best 3
    reranked_chunks = rerank_chunks(
        query=request.question,
        chunks=candidates,
        top_k=request.top_k  # Usually 3
    )
    
    # Step 3: Format for LLM
    formatted_chunks = [
        {
            "chunk_index": chunk["chunk_index"],
            "text": chunk["text"],
            "hybrid_score": chunk["hybrid_score"],
            "rerank_score": chunk["rerank_score"]  # Show both scores
        }
        for chunk in reranked_chunks
    ]
    
    # Step 4: Generate answer with LLM
    print("🤖 Generating answer...")
    from app.llm import generate_answer
    answer = generate_answer(request.question, formatted_chunks)
    
    return {
        "question": request.question,
        "contract_id": request.contract_id,
        "answer": answer,
        "sources": formatted_chunks,
        "search_type": "hybrid + reranking"  # Updated
    }