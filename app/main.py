from fastapi import FastAPI
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth_routes import router as auth_router

app = FastAPI(
    title="Legal Document Analysis API",
    description="""API for analyzing legal contracts, agreements, business documents, research papers, and similar formal documents using LLMs and vector search.""",
    version="1.0.0"
)

# ADD CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes
app.include_router(router)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Legal Document Analysis API",
        "version": "1.0.0"
    }