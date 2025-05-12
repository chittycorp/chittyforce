#!/usr/bin/env python3
"""
Simple test for running and accessing the server endpoint
"""
import os
import sys
import time
import threading
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simple_test")

def main():
    """Run a simple server test"""
    # Kill any existing processes
    logger.info("Killing any existing processes")
    subprocess.run("pkill -f uvicorn || true", shell=True)
    
    # Start the server
    logger.info("Starting uvicorn server")
    uvicorn_cmd = "python -m uvicorn main:app --host 127.0.0.1 --port 5000"
    server_process = subprocess.Popen(
        uvicorn_cmd, 
        shell=True, 
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Wait for server to start
    logger.info("Waiting for server to start")
    time.sleep(3)
    
    # Check if server is still running
    if server_process.poll() is not None:
        logger.error("Server failed to start")
        return 1
    
    # Make a request to the health endpoint
    logger.info("Making request to health endpoint")
    health_cmd = "curl -s http://127.0.0.1:5000/health"
    health_result = subprocess.run(health_cmd, shell=True, capture_output=True, text=True)
    
    if health_result.returncode != 0:
        logger.error(f"Health request failed: {health_result.stderr}")
    else:
        logger.info(f"Health response: {health_result.stdout}")
    
    # Make a request to the API info endpoint
    logger.info("Making request to API endpoint")
    api_cmd = "curl -s http://127.0.0.1:5000/api"
    api_result = subprocess.run(api_cmd, shell=True, capture_output=True, text=True)
    
    if api_result.returncode != 0:
        logger.error(f"API request failed: {api_result.stderr}")
    else:
        logger.info(f"API response: {api_result.stdout}")
        
    # Success if both requests succeeded
    result = health_result.returncode == 0 and api_result.returncode == 0
        
    # Stop the server
    logger.info("Stopping server")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning("Server didn't terminate gracefully, killing")
        server_process.kill()
        server_process.wait()
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main())