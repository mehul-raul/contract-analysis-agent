from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, Dict

_llm = None

def get_llm():
    """Get or initialize LLM"""
    global _llm
    if _llm is None:
        print("🤖 Loading Gemini LLM...")
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3
        )
        print("✅ LLM loaded")
    return _llm

def generate_answer(question: str, chunks: List[Dict]) -> str:
    """
    Generate answer from chunks
    
    Args:
        question: User question
        chunks: Retrieved chunks from vector search
    
    Returns:
        Answer string
    """
    llm = get_llm()
    
    # Build context
    context = "\n\n".join([
        f"[Section {i+1}]:\n{chunk['text']}"
        for i, chunk in enumerate(chunks)
    ])
    
    # Build prompt
    prompt_template = ChatPromptTemplate([
    ("system", """You are an AI assistant.
    - Answer using ONLY the context below
    - If not in context, say "Not found in the document"
    - Be concise
    
    Context:
    {context}"""),  # Move {context} to its own line for clarity
    ("human", "{question}")  # Just the question, cleaner
    ])
#     prompt = f"""You are analyzing a document. Answer based ONLY on the context below.

# Context:
# {context}

# Question: {question}

# Instructions:
# - Answer using ONLY the context above
# - Cite which section you used (e.g., "According to Section 1...")
# - If not in context, say "Not found in the document"
# - Be concise

# Answer:"""
    

    prompt = prompt_template.invoke({"context": context, "question": question})
    # Generate
    response = llm.invoke(prompt)
    return response.content