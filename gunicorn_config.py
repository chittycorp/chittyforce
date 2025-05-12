"""
Gunicorn configuration to use with FastAPI
"""
import multiprocessing
import os

# Gunicorn app configuration
wsgi_app = "wsgi:application"
bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
reload = True
reload_extra_files = ["templates"]

# Logging configuration
loglevel = "info"
accesslog = "-"
errorlog = "-"