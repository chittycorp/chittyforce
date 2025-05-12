import os
import logging
import json
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Universal Connector Configuration
UNIVERSAL_CONNECTOR_URL = os.environ.get("UNIVERSAL_CONNECTOR_URL", "https://universalconnector.replit.app")
UNIVERSAL_CONNECTOR_KEY = os.environ.get("UNIVERSAL_CONNECTOR_KEY")

class ConnectorResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class KeyManager:
    """
    KeyManager handles interactions with the Universal Connector service
    to retrieve and manage API keys and secrets.
    """
    def __init__(self, base_url: str = None, api_key: str = None):
        """
        Initialize the KeyManager.
        
        Args:
            base_url: Base URL for the Universal Connector (optional, defaults to env var)
            api_key: API key for the Universal Connector (optional, defaults to env var)
        """
        self.base_url = base_url or UNIVERSAL_CONNECTOR_URL
        self.api_key = api_key or UNIVERSAL_CONNECTOR_KEY
        
        if not self.base_url:
            logger.warning("Universal Connector URL not configured")
        
        if not self.api_key:
            logger.warning("Universal Connector API key not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authorization."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}" if self.api_key else ""
        }
    
    def get_key(self, key_name: str) -> ConnectorResponse:
        """
        Retrieve a key from the Universal Connector.
        
        Args:
            key_name: The name of the key to retrieve
            
        Returns:
            ConnectorResponse with success status and data or error
        """
        if not self.base_url or not self.api_key:
            return ConnectorResponse(
                success=False,
                error="Universal Connector not configured"
            )
        
        try:
            response = requests.get(
                f"{self.base_url}/api/keys/{key_name}",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return ConnectorResponse(
                    success=True,
                    data={"key": data.get("key"), "name": key_name}
                )
            else:
                logger.error(f"Failed to retrieve key {key_name}: {response.status_code}")
                return ConnectorResponse(
                    success=False,
                    error=f"Failed to retrieve key: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error retrieving key {key_name}: {str(e)}")
            return ConnectorResponse(
                success=False,
                error=f"Error retrieving key: {str(e)}"
            )
    
    def store_key(self, key_name: str, key_value: str) -> ConnectorResponse:
        """
        Store a key in the Universal Connector.
        
        Args:
            key_name: The name to store the key under
            key_value: The key value to store
            
        Returns:
            ConnectorResponse with success status and data or error
        """
        if not self.base_url or not self.api_key:
            return ConnectorResponse(
                success=False,
                error="Universal Connector not configured"
            )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/keys",
                headers=self._get_headers(),
                json={"name": key_name, "key": key_value},
                timeout=10
            )
            
            if response.status_code in (200, 201):
                return ConnectorResponse(
                    success=True,
                    data={"name": key_name, "message": "Key stored successfully"}
                )
            else:
                logger.error(f"Failed to store key {key_name}: {response.status_code}")
                return ConnectorResponse(
                    success=False,
                    error=f"Failed to store key: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error storing key {key_name}: {str(e)}")
            return ConnectorResponse(
                success=False,
                error=f"Error storing key: {str(e)}"
            )
    
    def list_keys(self) -> ConnectorResponse:
        """
        List all available keys in the Universal Connector.
        
        Returns:
            ConnectorResponse with success status and data or error
        """
        if not self.base_url or not self.api_key:
            return ConnectorResponse(
                success=False,
                error="Universal Connector not configured"
            )
        
        try:
            response = requests.get(
                f"{self.base_url}/api/keys",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return ConnectorResponse(
                    success=True,
                    data={"keys": data.get("keys", [])}
                )
            else:
                logger.error(f"Failed to list keys: {response.status_code}")
                return ConnectorResponse(
                    success=False,
                    error=f"Failed to list keys: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error listing keys: {str(e)}")
            return ConnectorResponse(
                success=False,
                error=f"Error listing keys: {str(e)}"
            )
    
    def delete_key(self, key_name: str) -> ConnectorResponse:
        """
        Delete a key from the Universal Connector.
        
        Args:
            key_name: The name of the key to delete
            
        Returns:
            ConnectorResponse with success status and data or error
        """
        if not self.base_url or not self.api_key:
            return ConnectorResponse(
                success=False,
                error="Universal Connector not configured"
            )
        
        try:
            response = requests.delete(
                f"{self.base_url}/api/keys/{key_name}",
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code in (200, 204):
                return ConnectorResponse(
                    success=True,
                    data={"name": key_name, "message": "Key deleted successfully"}
                )
            else:
                logger.error(f"Failed to delete key {key_name}: {response.status_code}")
                return ConnectorResponse(
                    success=False,
                    error=f"Failed to delete key: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error deleting key {key_name}: {str(e)}")
            return ConnectorResponse(
                success=False,
                error=f"Error deleting key: {str(e)}"
            )

# Initialize the key manager
key_manager = KeyManager()

def get_api_key() -> Optional[str]:
    """
    Get the API key from the Universal Connector or environment variables.
    
    Returns:
        The API key or None if not found
    """
    # First try environment variable
    api_key = os.environ.get("API_KEY")
    if api_key:
        return api_key
    
    # Then try Universal Connector
    response = key_manager.get_key("API_KEY")
    if response.success and response.data:
        return response.data.get("key")
    
    return None

def get_google_sa_key_json() -> Optional[str]:
    """
    Get the Google Service Account key from the Universal Connector or environment variables.
    
    Returns:
        The Google SA key JSON string or None if not found
    """
    # First try environment variable
    key_file = os.environ.get("GOOGLE_SA_KEY_FILE")
    if key_file and os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading Google SA key file: {str(e)}")
    
    # Try direct JSON in env var
    key_json = os.environ.get("GOOGLE_SA_KEY_JSON")
    if key_json:
        return key_json
    
    # Then try Universal Connector
    response = key_manager.get_key("GOOGLE_SA_KEY_JSON")
    if response.success and response.data:
        return response.data.get("key")
    
    return None

def get_notion_api_key() -> Optional[str]:
    """
    Get the Notion API key from the Universal Connector or environment variables.
    
    Returns:
        The Notion API key or None if not found
    """
    # First try environment variable
    api_key = os.environ.get("NOTION_API_KEY")
    if api_key:
        return api_key
    
    # Then try Universal Connector
    response = key_manager.get_key("NOTION_API_KEY")
    if response.success and response.data:
        return response.data.get("key")
    
    return None

def get_github_api_key() -> Optional[str]:
    """
    Get the GitHub API key from the Universal Connector or environment variables.
    
    Returns:
        The GitHub API key or None if not found
    """
    # First try environment variable
    api_key = os.environ.get("GITHUB_API_KEY")
    if api_key:
        return api_key
    
    # Then try Universal Connector
    response = key_manager.get_key("GITHUB_API_KEY")
    if response.success and response.data:
        return response.data.get("key")
    
    return None

def setup_google_sa_key_file() -> Optional[str]:
    """
    Setup Google Service Account key file from Universal Connector.
    Creates a temporary file with the JSON content.
    
    Returns:
        The path to the key file or None if not successful
    """
    key_json = get_google_sa_key_json()
    if not key_json:
        return None
    
    try:
        # Validate JSON structure
        json_data = json.loads(key_json)
        
        # Create a temp file to store the key
        temp_file = os.path.join(os.getcwd(), "google_sa_key.json")
        with open(temp_file, 'w') as f:
            f.write(key_json)
        
        # Set environment variable to point to this file
        os.environ["GOOGLE_SA_KEY_FILE"] = temp_file
        
        return temp_file
    except json.JSONDecodeError:
        logger.error("Invalid Google Service Account key JSON format")
        return None
    except Exception as e:
        logger.error(f"Error setting up Google SA key file: {str(e)}")
        return None