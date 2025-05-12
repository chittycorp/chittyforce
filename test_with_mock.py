#!/usr/bin/env python3
"""
Test script for Universal Connector with local mock

This script tests the integration with a local mock of the Universal Connector.
"""
import os
import json
import logging
import threading
import time
import sys
import requests
from mock_connector import app
import uvicorn
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("connector_test")

# Mock Connector Configuration
MOCK_PORT = 8000
MOCK_HOST = "127.0.0.1"
MOCK_URL = f"http://{MOCK_HOST}:{MOCK_PORT}"
MOCK_API_KEY = "mock_api_key_12345"  # Must match the one in mock_connector.py

@contextmanager
def mock_connector_server():
    """Start the mock connector server in a separate thread"""
    server_thread = threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": MOCK_HOST, "port": MOCK_PORT, "log_level": "error"}
    )
    
    server_thread.daemon = True
    server_thread.start()
    
    logger.info(f"Started mock connector server at {MOCK_URL}")
    
    # Wait for server to start
    for _ in range(5):
        try:
            response = requests.get(f"{MOCK_URL}/health")
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.5)
    else:
        logger.error("Failed to start mock connector server")
        sys.exit(1)
    
    # Set environment variables for connector
    os.environ["UNIVERSAL_CONNECTOR_URL"] = MOCK_URL
    os.environ["UNIVERSAL_CONNECTOR_KEY"] = MOCK_API_KEY
    
    try:
        yield
    finally:
        # We can't stop the uvicorn server cleanly, but it will terminate when the script ends
        logger.info("Mock connector server will terminate when script ends")

def run_tests():
    """Import and run the connector tests with mock environment"""
    from test_connector import run_all_tests
    
    # Run the connector tests
    success = run_all_tests()
    
    if success:
        logger.info("All tests passed with mock connector!")
        return 0
    else:
        logger.error("Some tests failed with mock connector")
        return 1

if __name__ == "__main__":
    with mock_connector_server():
        # Let's make a direct test to confirm the mock server is working
        try:
            headers = {"Authorization": f"Bearer {MOCK_API_KEY}"}
            response = requests.get(f"{MOCK_URL}/api/keys", headers=headers)
            
            if response.status_code == 200:
                keys = response.json().get("keys", [])
                logger.info(f"Mock connector has {len(keys)} keys: {', '.join(keys)}")
            else:
                logger.error(f"Failed to list keys: {response.status_code}")
        except Exception as e:
            logger.error(f"Error accessing mock connector: {str(e)}")
        
        # Run the actual tests
        sys.exit(run_tests())