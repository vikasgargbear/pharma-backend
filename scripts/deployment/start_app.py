#!/usr/bin/env python3
"""
Railway startup script that properly handles PORT
"""
import os
import sys
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting app on port: {port}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path[:3]}")
    
    uvicorn.run(
        "api.main:app",  # Switch back to full API
        host="0.0.0.0",
        port=port,
        log_level="info"
    )