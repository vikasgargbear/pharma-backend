#!/usr/bin/env python3
"""
Production server starter
"""
import os
import sys
import uvicorn

print(f"Starting server on port {os.environ.get('PORT', 8000)}")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting uvicorn on port {port}")
    
    try:
        uvicorn.run(
            "api.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",     # More logging to debug
            workers=1,
            access_log=True       # Enable access logs
        )
    except Exception as e:
        print(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)