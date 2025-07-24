#!/usr/bin/env python3
"""
Railway startup script with automatic migrations
"""
import os
import sys
import uvicorn

def run_migrations():
    """Run database migrations before starting the server"""
    print("🔄 Running database migrations...")
    try:
        from api.migrations.run_migrations import run_all_migrations
        success = run_all_migrations()
        if not success:
            print("⚠️  Some migrations failed, but continuing startup...")
    except Exception as e:
        print(f"⚠️  Migration runner error: {e}")
        print("   Continuing with startup anyway...")

if __name__ == "__main__":
    # Run migrations first
    run_migrations()
    
    # Start the server
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting AASO Pharma ERP on port: {port}")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )