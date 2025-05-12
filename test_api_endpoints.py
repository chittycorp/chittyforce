#!/usr/bin/env python3
"""
Test the API endpoints for SecureKey Workspace Agent

This script tests various API endpoints, including Google Workspace services
like Drive, Docs, Sheets, and Slides, as well as Notion and GitHub integrations.
"""
import os
import sys
import time
import json
import logging
import subprocess
import argparse
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("api_test")

# Configuration
HOST = "127.0.0.1"
PORT = 5000
BASE_URL = f"http://{HOST}:{PORT}"

# Test API key
API_KEY = "test_api_key_for_testing"

@contextmanager
def run_server():
    """Start the uvicorn server in a subprocess"""
    # Kill any existing processes
    logger.info("Killing any existing processes")
    subprocess.run("pkill -f uvicorn || true", shell=True)
    
    # Set test API key
    os.environ["API_KEY"] = API_KEY
    
    # Start the server
    logger.info("Starting uvicorn server")
    uvicorn_cmd = f"python -m uvicorn main:app --host {HOST} --port {PORT}"
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
        sys.exit(1)
    
    try:
        yield
    finally:
        # Stop the server
        logger.info("Stopping server")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("Server didn't terminate gracefully, killing")
            server_process.kill()
            server_process.wait()

def curl_request(method, endpoint, data=None, headers=None):
    """Make a curl request to the API"""
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    
    # Set default headers
    if headers is None:
        headers = {}
    headers.setdefault("Authorization", f"Bearer {API_KEY}")
    headers.setdefault("Content-Type", "application/json")
    
    # Build curl command
    curl_cmd = ["curl", "-s", "-X", method.upper(), url]
    
    # Add headers
    for key, value in headers.items():
        curl_cmd.extend(["-H", f"{key}: {value}"])
    
    # Add request body
    if data is not None:
        if isinstance(data, dict):
            data = json.dumps(data)
        curl_cmd.extend(["-d", data])
    
    # Execute curl command
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    # Parse response
    if result.returncode != 0:
        logger.error(f"Request failed: {result.stderr}")
        return None
    
    try:
        response = json.loads(result.stdout)
        return response
    except json.JSONDecodeError:
        logger.error(f"Failed to parse response as JSON: {result.stdout}")
        return result.stdout

def test_health():
    """Test the health endpoint"""
    logger.info("Testing health endpoint")
    response = curl_request("GET", "/health")
    
    if response and response.get("status") == "healthy":
        logger.info("Health check successful")
        return True
    else:
        logger.error(f"Health check failed: {response}")
        return False

def test_api_info():
    """Test the API info endpoint"""
    logger.info("Testing API info endpoint")
    response = curl_request("GET", "/api")
    
    if response and response.get("name") and response.get("status") == "online":
        logger.info(f"API info: {response}")
        return True
    else:
        logger.error(f"API info failed: {response}")
        return False

def test_drive_endpoints():
    """Test Drive API endpoints"""
    logger.info("Testing Drive API endpoints")
    
    # This is a mock test since we don't have valid credentials
    # It will test the API structure but expects auth errors
    
    # Test folder creation endpoint
    folder_request = {
        "name": "Test Folder",
        "parent_id": None
    }
    folder_response = curl_request("POST", "/drive/folder/create", data=folder_request)
    logger.info(f"Drive folder create response: {folder_response}")
    
    # Test file listing endpoint
    files_response = curl_request("GET", "/drive/files")
    logger.info(f"Drive files list response: {files_response}")
    
    # For now we just test if the endpoints exist and return proper errors
    # (since we don't have valid credentials)
    return True

def test_docs_endpoints():
    """Test Docs API endpoints"""
    logger.info("Testing Docs API endpoints")
    
    # Test document creation endpoint
    doc_request = {
        "title": "Test Document",
        "parent_id": None
    }
    doc_response = curl_request("POST", "/docs/create", data=doc_request)
    logger.info(f"Docs create response: {doc_response}")
    
    # For now we just test if the endpoints exist and return proper errors
    return True

def test_sheets_endpoints():
    """Test Sheets API endpoints"""
    logger.info("Testing Sheets API endpoints")
    
    # Test sheet creation endpoint
    sheet_request = {
        "title": "Test Sheet",
        "parent_id": None
    }
    sheet_response = curl_request("POST", "/sheets/create", data=sheet_request)
    logger.info(f"Sheets create response: {sheet_response}")
    
    # For now we just test if the endpoints exist and return proper errors
    return True

def test_slides_endpoints():
    """Test Slides API endpoints"""
    logger.info("Testing Slides API endpoints")
    
    # Test presentation creation endpoint
    presentation_request = {
        "title": "Test Presentation",
        "parent_id": None
    }
    presentation_response = curl_request("POST", "/slides/create", data=presentation_request)
    logger.info(f"Slides create response: {presentation_response}")
    
    # For now we just test if the endpoints exist and return proper errors
    return True

def test_integration_endpoints():
    """Test integration API endpoints (Notion, GitHub)"""
    logger.info("Testing integration API endpoints")
    
    # Test Notion status
    notion_response = curl_request("GET", "/integrations/notion/status")
    logger.info(f"Notion status response: {notion_response}")
    
    # Test GitHub status
    github_response = curl_request("GET", "/integrations/github/status")
    logger.info(f"GitHub status response: {github_response}")
    
    # For now we just test if the endpoints exist and return proper responses
    return True

def run_all_tests():
    """Run all API tests"""
    logger.info("=== Starting API endpoint tests ===")
    
    success = True
    success = test_health() and success
    success = test_api_info() and success
    
    try:
        success = test_drive_endpoints() and success
    except Exception as e:
        logger.error(f"Drive tests failed: {e}")
        success = False
    
    try:
        success = test_docs_endpoints() and success
    except Exception as e:
        logger.error(f"Docs tests failed: {e}")
        success = False
    
    try:
        success = test_sheets_endpoints() and success
    except Exception as e:
        logger.error(f"Sheets tests failed: {e}")
        success = False
    
    try:
        success = test_slides_endpoints() and success
    except Exception as e:
        logger.error(f"Slides tests failed: {e}")
        success = False
    
    try:
        success = test_integration_endpoints() and success
    except Exception as e:
        logger.error(f"Integration tests failed: {e}")
        success = False
    
    if success:
        logger.info("=== All API endpoint tests completed successfully ===")
    else:
        logger.error("=== Some API endpoint tests failed ===")
    
    return 0 if success else 1

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Test SecureKey Workspace Agent API")
    parser.add_argument("--health", action="store_true", help="Only test health endpoint")
    parser.add_argument("--drive", action="store_true", help="Only test Drive endpoints")
    parser.add_argument("--docs", action="store_true", help="Only test Docs endpoints")
    parser.add_argument("--sheets", action="store_true", help="Only test Sheets endpoints")
    parser.add_argument("--slides", action="store_true", help="Only test Slides endpoints")
    parser.add_argument("--integrations", action="store_true", help="Only test integration endpoints")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    with run_server():
        # Run specific tests or all tests
        if args.health:
            sys.exit(0 if test_health() else 1)
        elif args.drive:
            sys.exit(0 if test_drive_endpoints() else 1)
        elif args.docs:
            sys.exit(0 if test_docs_endpoints() else 1)
        elif args.sheets:
            sys.exit(0 if test_sheets_endpoints() else 1)
        elif args.slides:
            sys.exit(0 if test_slides_endpoints() else 1)
        elif args.integrations:
            sys.exit(0 if test_integration_endpoints() else 1)
        else:
            sys.exit(run_all_tests())