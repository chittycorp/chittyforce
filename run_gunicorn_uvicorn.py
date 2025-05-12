#!/usr/bin/env python3
"""
Run script using gunicorn with uvicorn workers for FastAPI

This script properly configures and starts a gunicorn server with uvicorn
workers for optimal compatibility with FastAPI in Replit environments.
"""
import os
import sys
import subprocess
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def kill_existing_servers():
    """Kill any existing uvicorn or gunicorn processes"""
    try:
        subprocess.run("pkill -f 'gunicorn|uvicorn'", shell=True)
    except Exception as e:
        logger.warning(f"Error killing existing processes: {e}")

def start_server():
    """Start gunicorn server with uvicorn workers for FastAPI application"""
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Configure gunicorn command
    cmd = [
        "gunicorn",
        "--worker-class", "uvicorn.workers.UvicornWorker",
        "--bind", "0.0.0.0:5000",
        "--workers", "1",
        "--reload",
        "asgi:application"
    ]
    
    logger.info(f"Starting server with command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd)
        
        # Setup signal handling
        def signal_handler(sig, frame):
            """Handle termination signals"""
            logger.info("Received termination signal. Shutting down...")
            process.terminate()
            process.wait()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait for process to complete
        process.wait()
        
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    kill_existing_servers()
    start_server()