from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, Contract, ContractChunk, User
from app.pdf_read_chunk import extract_text_from_pdf, chunk_text
from app.embeddingmaker import generate_many_embeddings, generate_embedding
from sqlalchemy import text
from pydantic import BaseModel, Field
from typing import Annotated
from app.auth import get_current_user
from app.llm import create_contract_agent, run_agent



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
    question: Annotated[str, Field(..., description="The question to ask")]
    top_k: Annotated[int, Field(5, description="Number of results")] = 5


@router.post("/query")  # Changed from /agent-query
def query_contract(
    request: QueryRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Query contract using intelligent agent.
    Agent decides whether to search contract, web, or both.
    """
    
    # Verify ownership
    contract = db.query(Contract).filter(
        Contract.id == request.contract_id,
        Contract.user_id == user_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found or you don't have access to it"
        )
    
    print(f"🤖 Agent query from user {user_id}: {request.question}")
    
    try:
        # Create agent with tools
        agent = create_contract_agent(db, request.contract_id)
        
        # Run agent (it decides which tools to use)
        answer = run_agent(agent, request.question)
        
        return {
            "question": request.question,
            "contract_id": request.contract_id,
            "answer": answer,
            "search_method": "agentic (hybrid + rerank + web)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    


@router.get("/my-contracts")
def list_my_contracts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    List all contracts uploaded by current user
    """
    contracts = db.query(Contract).filter(
        Contract.user_id == user_id
    ).all()
    
    return {
        "total": len(contracts),
        "contracts": [
            {
                "id": c.id,
                "filename": c.filename,
                "upload_date": c.upload_date.isoformat(),
                "num_chunks": c.num_chunks
            }
            for c in contracts
        ]
    }


@router.delete("/contracts/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Delete a specific contract (only if you own it)
    """
    
    # Verify ownership
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.user_id == user_id
    ).first()
    
    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contract not found or you don't own it"
        )
    
    # Delete chunks first (foreign key constraint)
    db.query(ContractChunk).filter(
        ContractChunk.contract_id == contract_id
    ).delete()
    
    # Delete contract
    db.delete(contract)
    db.commit()
    
    return {
        "message": f"Contract '{contract.filename}' deleted successfully",
        "contract_id": contract_id
    }


@router.delete("/my-contracts/all")
def delete_all_my_contracts(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user)
):
    """
    Delete ALL contracts uploaded by current user
    """
    
    # Get user's contracts
    user_contracts = db.query(Contract).filter(
        Contract.user_id == user_id
    ).all()
    
    if not user_contracts:
        return {"message": "No contracts to delete"}
    
    # Delete all chunks for user's contracts
    for contract in user_contracts:
        db.query(ContractChunk).filter(
            ContractChunk.contract_id == contract.id
        ).delete()
    
    # Delete all contracts
    count = db.query(Contract).filter(
        Contract.user_id == user_id
    ).delete()
    
    db.commit()
    
    return {
        "message": f"Deleted {count} contracts successfully"
    }