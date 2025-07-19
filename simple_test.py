#!/usr/bin/env python3
"""Simple test to verify backend is Python/FastAPI"""

from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
def root():
    return {"message": "AASO Pharma Backend - Python/FastAPI Running!", "type": "fastapi"}

@app.get("/test")
def test():
    return {"status": "ok", "backend": "python", "framework": "fastapi"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)