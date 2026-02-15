from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import os
from app.database import init_db
from app.api.routes import router
from app.api.auth_routes import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not os.getenv("CI"):
        init_db()
    yield

app = FastAPI(
    title="Legal Document Analysis API",
    description="API for analyzing legal contracts, agreements, and research papers using LLMs.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development and frontend integration
# Ref: https://fastapi.tiangolo.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route registration
app.include_router(router)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "service": "Legal Document Analysis API",
        "version": "1.0.0"
    }