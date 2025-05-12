"""
ASGI application entry point for Gunicorn
"""
from main import app

# This makes the app compatible with Gunicorn
app = app