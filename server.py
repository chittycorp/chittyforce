"""
Server script to run the FastAPI application with uvicorn.

This is used instead of gunicorn for better compatibility with FastAPI.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")