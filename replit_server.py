#!/usr/bin/env python3
"""
Replit Server Launcher

This script serves as a reliable way to run our FastAPI application in Replit.
It directly uses uvicorn, which is the recommended ASGI server for FastAPI.
"""
import os
import sys
import logging
import uvicorn
import signal
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("replit_server")

def run_server():
    """Run the FastAPI application with uvicorn"""
    try:
        logger.info("Starting SecureKey FastAPI application with uvicorn")
        port = int(os.environ.get("PORT", 5000))
        
        # Configure signal handlers for graceful shutdown
        def handle_signal(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        
        # Configure and start uvicorn ASGI server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=True
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we're in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)