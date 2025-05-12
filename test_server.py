#!/usr/bin/env python3
"""
Test the server functionality by launching the server temporarily,
making a test request, and shutting it down.
"""
import os
import sys
import time
import threading
import logging
import requests
import signal
import subprocess
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("server_test")

# Server configuration
HOST = "127.0.0.1"
PORT = 5000
SERVER_URL = f"http://{HOST}:{PORT}"

@contextmanager
def run_server():
    """Start the uvicorn server in a subprocess"""
    # Kill any existing processes
    subprocess.run("pkill -f uvicorn || true", shell=True)
    
    # Start the server
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", HOST,
        "--port", str(PORT)
    ]
    
    logger.info(f"Starting server: {' '.join(cmd)}")
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    def log_output():
        while process and process.poll() is None:
            line = process.stdout.readline().strip()
            if line:
                logger.info(f"Server: {line}")
                
    threading.Thread(target=log_output, daemon=True).start()
    
    # Wait for server to start
    for _ in range(10):
        if process.poll() is not None:
            stdout, _ = process.communicate()
            logger.error(f"Server failed to start: {stdout}")
            raise RuntimeError("Server failed to start")
            
        try:
            # Try to connect to the server
            requests.get(f"{SERVER_URL}/health", timeout=0.5)
            break
        except requests.RequestException:
            time.sleep(1)
    else:
        logger.error("Server didn't start within the timeout period")
        process.terminate()
        process.wait()
        raise TimeoutError("Server didn't start within the timeout period")
    
    # Server is running
    logger.info(f"Server running at {SERVER_URL}")
    
    try:
        # Return control to test function
        yield
    finally:
        # Terminate the server
        logger.info("Stopping server")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Server didn't terminate gracefully, killing...")
            process.kill()
            process.wait()

def test_health_endpoint():
    """Test the /health endpoint"""
    logger.info("Testing /health endpoint")
    
    try:
        response = requests.get(f"{SERVER_URL}/health")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Health check successful: {data}")
            return True
        else:
            logger.error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error testing health endpoint: {e}")
        return False

def test_api_info():
    """Test the API info endpoint"""
    logger.info("Testing /api endpoint")
    
    try:
        response = requests.get(f"{SERVER_URL}/api")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API info: {data}")
            return True
        else:
            logger.error(f"API info failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error testing API info: {e}")
        return False

def run_tests():
    """Run all server tests"""
    logger.info("=== Starting server tests ===")
    
    with run_server():
        # Run the tests
        success = test_health_endpoint() and test_api_info()
        
    if success:
        logger.info("=== All server tests passed ===")
        return 0
    else:
        logger.error("=== Some server tests failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())