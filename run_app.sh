#!/bin/bash
# Start the FastAPI application using uvicorn directly

# Kill any existing servers
pkill -f gunicorn || true
pkill -f uvicorn || true

# Change to the project directory
cd "$(dirname "$0")"

echo "Starting FastAPI application with uvicorn..."
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload