#!/usr/bin/env python3
"""
Railway startup script that properly handles PORT
"""
import os
import sys
import uvicorn

# Get the project root directory (two levels up from scripts/deployment/)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(f"Script location: {__file__}")
print(f"Project root: {project_root}")

# Change to project root directory
os.chdir(project_root)
print(f"Changed working directory to: {os.getcwd()}")

# Add project root to Python path
sys.path.insert(0, project_root)
print(f"Python path: {sys.path[:3]}")

# Verify api module can be found
try:
    import api
    print(f"✅ api module found at: {api.__file__}")
except ImportError as e:
    print(f"❌ api module not found: {e}")
    print(f"Directory contents: {os.listdir('.')}")
    raise

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting app on port: {port}")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )