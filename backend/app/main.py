"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router
from .core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Crime Risk Prediction API",
    description="Predict crime risk zones using environmental data",
    version="1.0.0",
    debug=settings.DEBUG
)

# CORS middleware - adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["risk"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Crime Risk Prediction API",
        "version": "1.0.0",
        "docs": "/docs"
    }