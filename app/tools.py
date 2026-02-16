from langchain.tools import tool
from langchain_tavily import TavilySearch
from sqlalchemy.orm import Session
from app.hybrid_search import hybrid_search, rerank_chunks
from app.database import Contract
from typing import Dict, List


# ---------------------------
# Web Search Tool
# ---------------------------

def create_web_search_tool():
    return TavilySearch(
        max_results=3,
        search_depth="basic"
    )


# ---------------------------
# Single Contract Search Tool
# ---------------------------

def create_contract_search_tool(db: Session, contract_id: int):
    """Search a specific contract (legacy - for backwards compatibility)"""

    @tool
    def search_contract(query: str) -> str:
        """
        Search the user's uploaded contract using hybrid search + reranking.
        Use this when the question is about the uploaded contract.
        
        Returns detailed information with source attribution.
        """

        try:
            # Hybrid search
            print(f"🔍 Running hybrid search for: {query}")
            candidates = hybrid_search(
                db=db,
                query=query,
                contract_id=contract_id,
                top_k=10
            )

            if not candidates:
                return "No relevant information found in the contract."

            # Rerank
            print(f"🎯 Reranking {len(candidates)} candidates...")
            reranked = rerank_chunks(query, candidates, top_k=5)

            # Format results
            result = "Found the following relevant sections from the contract:\n\n"
            for i, chunk in enumerate(reranked, 1):
                result += f"[Section {i}] (Relevance: {chunk.get('rerank_score', 0):.2f}):\n"
                result += f"{chunk['text']}\n\n"

            return result

        except Exception as e:
            return f"Error searching contract: {str(e)}"

    return search_contract


# ---------------------------
# Multi-Document Search Tool (NEW)
# ---------------------------

def create_multi_document_search_tool(db: Session, user_id: int):
    """
    Search across ALL user's documents intelligently.
    This is the MAIN tool for document queries.
    """
    
    @tool
    def search_all_my_documents(query: str) -> str:
        """
        Search across ALL documents uploaded by the user.
        Use this when the user asks about their contracts, documents, files, or any content they uploaded.
        
        Examples:
        - "What does my contract say?"
        - "Summarize all my documents"
        - "What termination clauses do I have?"
        - "Search my files for payment terms"
        
        Args:
            query: The search query
            
        Returns:
            Relevant information from all user's documents with source attribution
        """
        
        try:
            # Get all user's contracts
            user_contracts = db.query(Contract).filter(
                Contract.user_id == user_id
            ).all()
            
            if not user_contracts:
                return "❌ You have no documents uploaded yet. Please upload a PDF document first, then I can help analyze it!"
            
            print(f"📚 Searching across {len(user_contracts)} document(s)")
            
            # Search across all contracts
            all_results = []
            
            for contract in user_contracts:
                try:
                    # Hybrid search on this contract
                    candidates = hybrid_search(db, query, contract.id, top_k=5)
                    
                    if candidates:
                        # Rerank
                        reranked = rerank_chunks(query, candidates, top_k=3)
                        
                        # Add source info
                        for chunk in reranked:
                            chunk['source_document'] = contract.filename
                            chunk['contract_id'] = contract.id
                        
                        all_results.extend(reranked)
                        
                except Exception as e:
                    print(f"⚠️ Error searching {contract.filename}: {str(e)}")
                    continue
            
            if not all_results:
                doc_names = [c.filename for c in user_contracts]
                return f"❌ No relevant information found in your {len(user_contracts)} document(s): {', '.join(doc_names)}"
            
            # Sort by relevance score
            all_results.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
            
            # Take top 5 across all documents
            top_results = all_results[:5]
            
            # Format results
            result = f"✅ Found relevant information across your documents:\n\n"
            
            for i, chunk in enumerate(top_results, 1):
                result += f"--- Result {i} ---\n"
                result += f"📄 Source: {chunk['source_document']}\n"
                result += f"📊 Relevance: {chunk.get('rerank_score', 0):.2f}\n\n"
                result += f"{chunk['text']}\n\n"
            
            return result
            
        except Exception as e:
            return f"❌ Error searching documents: {str(e)}"
    
    return search_all_my_documents