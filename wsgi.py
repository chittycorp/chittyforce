"""
WSGI adapter for FastAPI application
This file provides a WSGI-compatible interface to the FastAPI application.
"""
import logging
from asgiref.wsgi import WsgiToAsgi
from main import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create WSGI application from ASGI application
wsgi_app = WsgiToAsgi(app)

# Make the WSGI application available to Gunicorn
application = wsgi_app

if __name__ == "__main__":
    # For local development
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)