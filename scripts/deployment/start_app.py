#!/usr/bin/env python3
"""
Railway startup script that properly handles PORT
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting app on port: {port}")
    
    uvicorn.run(
        "api.main:app",  # Switch back to full API
        host="0.0.0.0",
        port=port,
        log_level="info"
    )