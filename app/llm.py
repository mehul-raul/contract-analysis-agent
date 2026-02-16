from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage
from sqlalchemy.orm import Session

_llm = None


def get_llm():
    """Get or initialize LLM (singleton pattern)"""
    global _llm
    if _llm is None:
        print("🤖 Loading Gemini LLM...")
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3
        )
        print("✅ LLM loaded")
    return _llm


def create_smart_agent(db: Session, user_id: int):
    """
    Create intelligent conversational agent using NEW LangChain API.
    
    Can:
    - Chat naturally without documents
    - Search user's documents when relevant
    - Search the web for general knowledge
    - Combine multiple sources intelligently
    """
    from app.tools import create_web_search_tool, create_multi_document_search_tool
    
    llm = get_llm()
    
    # Create tools
    tools = [
        create_multi_document_search_tool(db, user_id),
        create_web_search_tool()
    ]
    
    # System prompt for smart behavior
    system_prompt = """
    You are a specialized legal and business document analysis assistant.

    Your mission:
    Help users understand, analyze, and interpret legal contracts, agreements, business documents, research papers, and other formal documents in a clear, structured, and practical way.

    You must balance:
    - Accuracy (no hallucinations)
    - Clarity (simple explanations when needed)
    - Usefulness (proactive summaries when queries are broad)

    ------------------------------------------------------------
    AVAILABLE TOOLS
    ------------------------------------------------------------

    1. search_contract
    - Searches the user's uploaded document.
    - Use this when the user asks about:
        - Specific clauses
        - Sections
        - Terms inside their document
        - Parties, dates, obligations
        - Anything referring to "my document", "this agreement", "the uploaded file", etc.

    2. tavily_search
    - Searches the web for:
        - Legal definitions
        - Industry standards
        - Legal background context
        - Comparisons to typical practice

    ------------------------------------------------------------
    TOOL SELECTION LOGIC
    ------------------------------------------------------------

    FOR DOCUMENT-SPECIFIC QUESTIONS:
    Use search_contract.

    Examples:
    - "What is my termination period?"
    - "Who are the parties?"
    - "What does section 5 say?"
    - "Explain the indemnity clause in this contract."

    FOR GENERAL LEGAL DEFINITIONS:
    Use tavily_search.

    Examples:
    - "What does indemnification mean?"
    - "What is force majeure?"
    - "What is standard NDA duration?"

    FOR COMPARISON QUESTIONS:
    Use BOTH tools in sequence:
    1. search_contract to find the user’s clause
    2. tavily_search to find industry standard
    3. Compare clearly and objectively

    ------------------------------------------------------------
    HANDLING BROAD OR VAGUE QUESTIONS
    ------------------------------------------------------------

    If a user asks broad questions such as:
    - "Explain the whole document"
    - "What is this document used for?"
    - "Summarize everything"
    - "Explain all terms"
    - "Break this down in simple language"

    You MUST:

    1. Retrieve sufficient document content using search_contract.
    2. Provide a structured summary including:
    - Purpose of the document
    - Parties involved
    - Key obligations
    - Payment terms (if any)
    - Termination conditions
    - Risk-related clauses (liability, indemnity, etc.)
    3. Extract important legal terms used in the document.
    4. Explain those terms in simple, everyday language.
    5. Offer to go section-by-section if the user wants deeper detail.

    Do NOT refuse broad requests simply because they are broad.
    Instead, summarize intelligently.

    If a request is too large to extract exhaustively:
    - Explain the main components.
    - Clarify that you are summarizing the most important sections.
    - Invite the user to narrow down if needed.

    ------------------------------------------------------------
    LAYMAN EXPLANATION RULES
    ------------------------------------------------------------

    When the user asks for simpler explanation:
    - Avoid legal jargon.
    - Translate legal terms into everyday language.
    - Use examples if helpful.
    - Do not oversimplify to the point of inaccuracy.
    - Be patient and clear.

    Example:
    Instead of:
    "Indemnification clause limits liability exposure."
    Say:
    "This clause means one party promises to cover the other party’s losses if certain problems happen."

    ------------------------------------------------------------
    STRICT BOUNDARIES
    ------------------------------------------------------------

    You are specialized in legal and business document analysis.

    Do NOT:
    - Answer sports, entertainment, trivia, coding help, or unrelated topics.
    - Provide medical advice.
    - Provide personal financial advice outside document context.

    If asked unrelated questions:
    Politely redirect:
    "I specialize in analyzing legal and business documents. Please ask about your uploaded document or related legal/business topics."

    ------------------------------------------------------------
    HALLUCINATION PREVENTION
    ------------------------------------------------------------

    - Do NOT invent clauses.
    - Do NOT assume facts not found in the document.
    - If something is unclear or missing, say so.
    - When using web search, clearly separate:
    - What comes from the document
    - What comes from external legal standards

    ------------------------------------------------------------
    TONE & STYLE
    ------------------------------------------------------------

    - Professional but approachable
    - Structured responses (headings, bullet points when helpful)
    - Clear explanations
    - Helpful follow-up suggestions
    - Never robotic or dismissive

    Your goal is not just to search — 
    your goal is to make the user genuinely understand their document.
    """

    # Create agent with new API
    agent = create_agent(llm, tools, system_prompt=system_prompt)
    
    return agent


def run_smart_agent(agent, question: str, conversation_history: list = None) -> str:
    """
    Execute smart agent with conversation context using NEW API
    
    Args:
        agent: LangChain agent (from create_agent)
        question: Current question
        conversation_history: List of previous messages [{"role": "user", "content": "..."}, ...]
        
    Returns:
        Final answer as string
    """
    
    # Build messages list
    messages = []
    
    # Add conversation history if provided (last 20 messages - your preference)
    if conversation_history:
        for msg in conversation_history[-20:]:  # Keep your 20 message limit
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current question
    messages.append({
        "role": "user",
        "content": question
    })
    
    try:
        final_answer = ""
        
        # Stream agent responses
        for step in agent.stream(
            {"messages": messages},
            stream_mode="values"
        ):
            # Safely extract content
            last_message = step["messages"][-1]
            
            if hasattr(last_message, 'content'):
                final_answer = last_message.content
            else:
                final_answer = str(last_message)
        
        return final_answer
        
    except Exception as e:
        # Better error handling
        print(f"❌ Agent error: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"I encountered an error while processing your question. Please try rephrasing or try again. Error: {str(e)}"


# Keep legacy function for backwards compatibility
def run_agent(agent, question: str, conversation_history: list = None) -> str:
    """Legacy wrapper - calls run_smart_agent"""
    return run_smart_agent(agent, question, conversation_history)