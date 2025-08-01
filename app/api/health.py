"""
Health check endpoints
"""
from fastapi import APIRouter, HTTPException
from app.core.database import test_connection
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "pharma-backend",
        "version": "2.0.0"
    }

@router.get("/health/db")
async def database_health():
    """Database connectivity check"""
    if test_connection():
        return {
            "status": "healthy",
            "database": "connected",
            "host": os.getenv("DATABASE_URL", "").split("@")[1].split(":")[0] if "@" in os.getenv("DATABASE_URL", "") else "unknown"
        }
    else:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )