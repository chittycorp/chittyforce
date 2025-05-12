#!/usr/bin/env python3
"""
Mock Universal Connector for local testing

This script implements a simple FastAPI server that mimics the behavior
of the Universal Connector service for local development and testing.
"""
import os
import json
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mock_connector")

# Create FastAPI app
app = FastAPI(
    title="Mock Universal Connector",
    description="A mock service for testing the Universal Connector integration",
    version="1.0.0"
)

# Mock data storage (in-memory database)
keys_db = {}

# API key for access control
ADMIN_API_KEY = "mock_api_key_12345"

# Models
class KeyRequest(BaseModel):
    name: str
    key: str

class KeyResponse(BaseModel):
    key: str

class KeysListResponse(BaseModel):
    keys: List[str]

# Authentication function
def verify_api_key(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )
    
    token = authorization.replace("Bearer ", "")
    
    if token != ADMIN_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return token

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/keys", response_model=KeysListResponse)
async def list_keys(api_key: str = Depends(verify_api_key)):
    """List all available keys"""
    return {"keys": list(keys_db.keys())}

@app.get("/api/keys/{key_name}", response_model=KeyResponse)
async def get_key(key_name: str, api_key: str = Depends(verify_api_key)):
    """Get a specific key by name"""
    if key_name not in keys_db:
        raise HTTPException(
            status_code=404,
            detail=f"Key '{key_name}' not found"
        )
    
    return {"key": keys_db[key_name]}

@app.post("/api/keys", status_code=201)
async def create_key(request: KeyRequest, api_key: str = Depends(verify_api_key)):
    """Create or update a key"""
    keys_db[request.name] = request.key
    return {"message": f"Key '{request.name}' stored successfully"}

@app.delete("/api/keys/{key_name}", status_code=204)
async def delete_key(key_name: str, api_key: str = Depends(verify_api_key)):
    """Delete a key"""
    if key_name not in keys_db:
        raise HTTPException(
            status_code=404,
            detail=f"Key '{key_name}' not found"
        )
    
    del keys_db[key_name]
    return None

@app.on_event("startup")
async def startup_event():
    """Initialize with some default keys for testing"""
    logger.info("Initializing mock connector with default keys")
    
    # Add some default keys
    keys_db["API_KEY"] = "mock_api_key_1"
    keys_db["GOOGLE_SA_KEY_JSON"] = json.dumps({
        "type": "service_account",
        "project_id": "mock-project-123",
        "private_key_id": "mock-key-id-123",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_KEY_CONTENT\n-----END PRIVATE KEY-----\n",
        "client_email": "mock@mock-project-123.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock%40mock-project-123.iam.gserviceaccount.com"
    })
    keys_db["NOTION_API_KEY"] = "mock_notion_key_1"
    keys_db["GITHUB_API_KEY"] = "mock_github_key_1"
    
    logger.info(f"Added {len(keys_db)} default keys")

def run_server():
    """Run the mock connector server"""
    logger.info("Starting mock Universal Connector server")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()