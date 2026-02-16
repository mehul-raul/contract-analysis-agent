from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.auth_routes import router as auth_router

app = FastAPI(
    title="Legal Document Analysis API",
    description="API for analyzing legal contracts, agreements, and research papers using LLMs.",
    version="1.0.0"
)

# CORS - MUST be added FIRST before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "Legal Document Analysis API",
        "version": "1.0.0"
    }