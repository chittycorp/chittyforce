"""
ASGI application entry point for Gunicorn
"""
from main import app

# This is the ASGI application that Gunicorn will use
application = app