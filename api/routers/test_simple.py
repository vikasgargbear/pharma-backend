"""
Simple test router to verify basic functionality
"""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/test", tags=["test"])

@router.get("/")
async def test_root():
    """Simple test endpoint"""
    return {
        "message": "Test endpoint working",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/echo")
async def test_echo(data: dict):
    """Echo back any JSON data"""
    return {
        "echo": data,
        "received_at": datetime.utcnow().isoformat()
    }