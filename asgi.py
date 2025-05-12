"""
ASGI application entry point for Gunicorn

This adapter ensures proper ASGI compatibility between Gunicorn and FastAPI.
"""
import os
from main import app
import uvicorn.workers

# This is the ASGI application that Gunicorn will use
application = app

# Make application available for uvicorn worker
__all__ = ['application']

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run("asgi:application", host="0.0.0.0", port=port)