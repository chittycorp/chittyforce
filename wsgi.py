"""
WSGI adapter for FastAPI to work with gunicorn
"""
from fastapi.applications import FastAPI
from main import app as fastapi_app

# Create WSGI application
application = fastapi_app