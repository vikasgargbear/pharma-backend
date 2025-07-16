#!/usr/bin/env python3
"""
Production server starter - Memory optimized for Render
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",  # Reduce logging
        workers=1,            # Single worker for memory efficiency
        access_log=False      # Disable access logs
    )