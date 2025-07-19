#!/usr/bin/env python3
"""
Simple Railway startup script
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting AASO Pharma ERP on port: {port}")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )