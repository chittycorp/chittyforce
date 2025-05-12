"""
Server script to run the FastAPI application with uvicorn.

This is used instead of gunicorn for better compatibility with FastAPI.
"""
import os
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Set up logger
    logger = logging.getLogger("server")
    logger.info("Starting FastAPI application with uvicorn")
    
    # Get port from environment or use default
    port = int(os.environ.get("PORT", "5000"))
    logger.info(f"Server will listen on port {port}")
    
    # Run the application with uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=port, 
        reload=True,
        log_level="info"
    )