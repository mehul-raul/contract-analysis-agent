from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from sqlalchemy.orm import Session

_llm = None


def get_llm():
    """Get or initialize LLM (singleton pattern)"""
    global _llm
    if _llm is None:
        print("🤖 Loading Gemini LLM...")
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.3
        )
        print("✅ LLM loaded")
    return _llm


def create_contract_agent(db: Session, contract_id: int):
    """
    Create agent with contract search and web search tools
    """
    from app.tools import create_web_search_tool, create_contract_search_tool
    
    llm = get_llm()
    
    # Create tools
    tools = [
        create_contract_search_tool(db, contract_id),
        create_web_search_tool()
    ]
    
    # System prompt using ChatPromptTemplate style
    system_prompt = """You are a specialized legal and business document analysis assistant.

    Your purpose: Help users understand and analyze legal contracts, agreements, business documents, research papers, and similar formal documents.

    Available tools:
    1. search_contract - Searches the user's uploaded document (contract, agreement, paper, report, etc.)
    2. tavily_search - Searches the web for legal definitions, industry standards, similar cases, or additional context

    Tool selection rules:

    FOR DOCUMENT-SPECIFIC QUERIES (use search_contract):
    - User mentions: "my document", "the contract", "this agreement", "the paper I uploaded", "my NDA", "this file", "my pdf" or any thing similar
    - Questions about: specific clauses, terms, conditions, sections, parties, dates, obligations in THEIR document
    - Examples: "What is my termination period?", "Who are the parties?", "What does section 5 say?"

    FOR EXTERNAL KNOWLEDGE (use tavily_search):
    - Legal definitions: "What does indemnification mean?", "Explain force majeure"
    - Industry standards: "What is standard notice period?", "Typical NDA duration"
    - Legal context: "What are my rights under labor law?", "Latest contract law changes"
    - Comparisons: "How does this compare to industry practice?"

    FOR COMPARISON QUERIES (use BOTH tools in sequence):
    - Pattern: "Is my X standard/common/typical or anything?"
    - Process: 
    1. First search_contract to find user's X
    2. Then tavily_search to find what's standard
    3. Compare and explain

    STRICT BOUNDARIES:
    - Do NOT answer: General trivia, sports, entertainment, personal advice, coding help
    - Stay focused on: Legal documents, contracts, agreements, business papers, formal documents
    - If asked unrelated questions: Politely redirect: "I'm specialized in analyzing legal and business documents. Please ask about your uploaded document or legal/business topics."

    Be professional, accurate, and cite sources when using web search."""
    
    # Create agent with system prompt
    agent = create_agent(llm, tools, system_prompt=system_prompt)
    
    return agent


def run_agent(agent, question: str) -> str:
    """
    Execute agent and return final answer
    
    Args:
        agent: LangChain agent
        question: User's question
        
    Returns:
        Final answer as string
    """
    final_answer = ""
    
    for step in agent.stream(
        {"messages": question},
        stream_mode="values"
    ):
        # Get the last message (final answer)
        final_answer = step["messages"][-1].content
    
    return final_answer