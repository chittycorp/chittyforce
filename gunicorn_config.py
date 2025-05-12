"""
Gunicorn configuration to use with FastAPI
"""
import multiprocessing
import os

# Gunicorn app configuration
wsgi_app = "asgi:application"  # Use our asgi application
bind = "0.0.0.0:5000"
workers = 1
worker_class = "uvicorn.workers.UvicornWorker"  # Use Uvicorn worker for ASGI compatibility
reload = True
reload_extra_files = ["templates"]

# Logging configuration
loglevel = "info"
accesslog = "-"
errorlog = "-"