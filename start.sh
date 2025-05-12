#!/bin/bash
# Start the FastAPI application using uvicorn directly
# This is more reliable than using gunicorn with FastAPI
echo "Starting FastAPI server with uvicorn..."
uvicorn main:app --host 0.0.0.0 --port 5000 --log-level info