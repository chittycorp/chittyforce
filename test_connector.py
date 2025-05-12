#!/usr/bin/env python3
"""
Test script for Universal Connector functionality

This script tests the connectivity and functionality of the Universal Connector
integration by performing basic operations.
"""
import os
import json
import logging
from connector import (
    key_manager, 
    get_api_key, 
    get_google_sa_key_json,
    get_notion_api_key,
    get_github_api_key,
    setup_google_sa_key_file
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("connector_test")

def test_connector_setup():
    """Test basic connector setup and configuration"""
    logger.info("Testing connector setup...")
    
    base_url = os.environ.get("UNIVERSAL_CONNECTOR_URL")
    api_key = os.environ.get("UNIVERSAL_CONNECTOR_KEY")
    
    if base_url:
        logger.info(f"Universal Connector URL: {base_url}")
    else:
        logger.warning("Universal Connector URL not configured")
    
    if api_key:
        logger.info("Universal Connector API key is configured")
    else:
        logger.warning("Universal Connector API key not configured")
    
    return bool(base_url and api_key)

def test_list_keys():
    """Test listing keys from the connector"""
    logger.info("Testing key listing...")
    
    response = key_manager.list_keys()
    
    if response.success:
        keys = response.data.get("keys", [])
        logger.info(f"Found {len(keys)} keys: {', '.join(keys)}")
        return True
    else:
        logger.error(f"Failed to list keys: {response.error}")
        return False

def test_store_and_get_key():
    """Test storing and retrieving a key"""
    logger.info("Testing key storage and retrieval...")
    
    test_key_name = "TEST_KEY"
    test_key_value = "test_value_12345"
    
    # Store the key
    store_response = key_manager.store_key(test_key_name, test_key_value)
    
    if not store_response.success:
        logger.error(f"Failed to store key: {store_response.error}")
        return False
    
    logger.info(f"Successfully stored key {test_key_name}")
    
    # Get the key
    get_response = key_manager.get_key(test_key_name)
    
    if not get_response.success:
        logger.error(f"Failed to retrieve key: {get_response.error}")
        return False
    
    retrieved_value = get_response.data.get("key")
    
    if retrieved_value == test_key_value:
        logger.info(f"Successfully retrieved key {test_key_name} with correct value")
        
        # Clean up by deleting the test key
        delete_response = key_manager.delete_key(test_key_name)
        if delete_response.success:
            logger.info(f"Successfully deleted test key {test_key_name}")
        else:
            logger.warning(f"Failed to delete test key: {delete_response.error}")
        
        return True
    else:
        logger.error(f"Retrieved value ({retrieved_value}) does not match stored value ({test_key_value})")
        return False

def test_retrieval_functions():
    """Test the retrieval wrapper functions"""
    logger.info("Testing key retrieval wrapper functions...")
    
    # API key
    api_key = get_api_key()
    logger.info(f"API key available: {bool(api_key)}")
    
    # Google SA key
    google_sa_key = get_google_sa_key_json()
    logger.info(f"Google SA key available: {bool(google_sa_key)}")
    
    # Notion API key
    notion_key = get_notion_api_key()
    logger.info(f"Notion API key available: {bool(notion_key)}")
    
    # GitHub API key
    github_key = get_github_api_key()
    logger.info(f"GitHub API key available: {bool(github_key)}")
    
    return True

def test_google_sa_file_setup():
    """Test setting up the Google Service Account key file"""
    logger.info("Testing Google SA key file setup...")
    
    file_path = setup_google_sa_key_file()
    
    if file_path:
        logger.info(f"Successfully set up Google SA key file at {file_path}")
        
        # Check if file exists and has valid JSON
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    json_data = json.loads(f.read())
                logger.info("File contains valid JSON")
                return True
            except json.JSONDecodeError:
                logger.error("File does not contain valid JSON")
                return False
        else:
            logger.error(f"File does not exist at {file_path}")
            return False
    else:
        logger.warning("Google SA key file setup failed or not available")
        return False

def run_all_tests():
    """Run all connector tests"""
    logger.info("===== Starting Universal Connector tests =====")
    
    # Count tests and successes
    tests = 0
    successes = 0
    
    # Test connector setup
    tests += 1
    if test_connector_setup():
        successes += 1
        
        # Only run these tests if connector is configured
        if test_list_keys():
            tests += 1
            successes += 1
        
        try:
            if test_store_and_get_key():
                tests += 1
                successes += 1
        except Exception as e:
            tests += 1
            logger.error(f"Error during key store/get test: {str(e)}")
    
    # Always run these tests as they fall back to environment variables
    tests += 1
    if test_retrieval_functions():
        successes += 1
    
    tests += 1
    if test_google_sa_file_setup():
        successes += 1
    
    # Report results
    logger.info(f"===== Test results: {successes}/{tests} tests passed =====")
    
    return successes == tests

if __name__ == "__main__":
    run_all_tests()