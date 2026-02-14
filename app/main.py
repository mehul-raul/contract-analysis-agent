from fastapi import FastAPI
from app.api.routes import router
from app.api.auth_routes import router as auth_router

app = FastAPI(title="contract-analysis-agent")

# Include the routes
app.include_router(router)
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}