"""
Reliable startup script for FastAPI using uvicorn directly.
This avoids the compatibility issues between FastAPI and gunicorn.
"""
import os
import sys
import subprocess
import signal
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("start_uvicorn")

def kill_existing_servers():
    """Kill any existing uvicorn or gunicorn processes"""
    try:
        logger.info("Attempting to kill existing server processes...")
        subprocess.run(["pkill", "-f", "gunicorn"], stderr=subprocess.PIPE)
        subprocess.run(["pkill", "-f", "uvicorn"], stderr=subprocess.PIPE)
        # Give processes time to shut down
        time.sleep(1)
        logger.info("Killed existing processes (if any)")
    except Exception as e:
        logger.warning(f"Error killing existing processes: {e}")

def start_server():
    """Start uvicorn server with FastAPI application"""
    port = int(os.environ.get("PORT", "5000"))
    host = "0.0.0.0"
    
    # Change to the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    logger.info(f"Starting FastAPI application on http://{host}:{port}")
    
    # Build the command to run
    cmd = [
        sys.executable, 
        "-m", 
        "uvicorn", 
        "main:app", 
        "--host", 
        host, 
        "--port", 
        str(port),
        "--reload"
    ]
    
    # Start the server
    server_process = subprocess.Popen(cmd)
    
    def signal_handler(sig, frame):
        """Handle termination signals"""
        logger.info("Received signal to shut down...")
        server_process.terminate()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Wait for server to complete
        server_process.wait()
    except KeyboardInterrupt:
        # Handle keyboard interrupt
        logger.info("Keyboard interrupt received. Shutting down...")
        server_process.terminate()

if __name__ == "__main__":
    kill_existing_servers()
    start_server()