"""
Gunicorn configuration to use with FastAPI via WSGI adapter
"""
import multiprocessing
import os

# Gunicorn app configuration
wsgi_app = "wsgi:application"  # Use our wsgi adapter application
bind = "0.0.0.0:5000"
workers = 1
reload = True
reload_extra_files = ["templates"]

# Logging configuration
loglevel = "info"
accesslog = "-"
errorlog = "-"