from langchain.tools import tool
from langchain_tavily import TavilySearch
from sqlalchemy.orm import Session
from app.hybrid_search import hybrid_search, rerank_chunks
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
# Contract Search Tool (UPDATED)
# ---------------------------

def create_contract_search_tool(db: Session, contract_id: int):

    @tool
    def search_contract(query: str) -> str:
        """
        Search the user's uploaded contract using hybrid search + reranking.
        Use this when the question is about the uploaded contract.
        
        Returns detailed information with source attribution.
        """

        try:
            # Step 1: Hybrid search (10 candidates)
            print(f"🔍 Running hybrid search for: {query}")
            candidates = hybrid_search(
                db=db,
                query=query,
                contract_id=contract_id,
                top_k=10
            )

            if not candidates:
                return "No relevant information found in the contract."

            # Step 2: Rerank to get best 5
            print(f"🎯 Reranking {len(candidates)} candidates...")
            reranked = rerank_chunks(query, candidates, top_k=5)

            # Step 3: Format results with scores
            result = "Found the following relevant sections from the contract:\n\n"
            for i, chunk in enumerate(reranked, 1):
                result += f"[Section {i}] (Hybrid Score: {chunk['hybrid_score']:.3f}, Rerank Score: {chunk['rerank_score']:.3f}):\n"
                result += f"{chunk['text']}\n\n"

            return result

        except Exception as e:
            return f"Error searching contract: {str(e)}"

    return search_contract