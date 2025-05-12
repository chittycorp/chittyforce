#!/bin/bash
# Run the FastAPI application using uvicorn
echo "Starting FastAPI application..."
python -m uvicorn main:app --host 0.0.0.0 --port 5000 --reload