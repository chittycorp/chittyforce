import os
import functools
import time
import json
from typing import Callable, Dict, Any, Optional
from fastapi import Request, HTTPException, Depends, Header
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)

# Constants
API_KEY_ENV_VAR = "API_KEY"
GOOGLE_SA_KEY_FILE_ENV_VAR = "GOOGLE_SA_KEY_FILE"
DEFAULT_API_KEY = None  # No default for security

# Error messages
MISSING_API_KEY_ERROR = "API key is required"
INVALID_API_KEY_ERROR = "Invalid API key"
MISSING_SA_CONFIG_ERROR = "Google service account configuration missing"
GOOGLE_API_ERROR = "Google API error"

# Cache for Google service clients
_services_cache = {}

def get_drive_service():
    """
    Get an authenticated Google Drive service client.
    
    Returns:
        A Google Drive v3 service object
    
    Raises:
        HTTPException: If service account configuration is missing or invalid
    """
    return _get_google_service('drive', 'v3', ["https://www.googleapis.com/auth/drive"])

def get_sheets_service():
    """
    Get an authenticated Google Sheets service client.
    
    Returns:
        A Google Sheets v4 service object
    
    Raises:
        HTTPException: If service account configuration is missing or invalid
    """
    return _get_google_service('sheets', 'v4', ["https://www.googleapis.com/auth/spreadsheets"])

def get_docs_service():
    """
    Get an authenticated Google Docs service client.
    
    Returns:
        A Google Docs v1 service object
    
    Raises:
        HTTPException: If service account configuration is missing or invalid
    """
    return _get_google_service('docs', 'v1', ["https://www.googleapis.com/auth/documents"])

def get_slides_service():
    """
    Get an authenticated Google Slides service client.
    
    Returns:
        A Google Slides v1 service object
    
    Raises:
        HTTPException: If service account configuration is missing or invalid
    """
    return _get_google_service('slides', 'v1', ["https://www.googleapis.com/auth/presentations"])

def _get_google_service(service_name, version, scopes):
    """
    Get a Google service client with authentication.
    Uses caching to avoid repeated initialization.
    
    Args:
        service_name: The name of the Google service
        version: The API version
        scopes: The OAuth scopes required
        
    Returns:
        A Google service object
        
    Raises:
        HTTPException: If service account configuration is missing or invalid
    """
    cache_key = f"{service_name}_{version}"
    
    # Return cached service if available
    if cache_key in _services_cache:
        return _services_cache[cache_key]
    
    # Get SA key file path from environment
    sa_key_file = os.getenv(GOOGLE_SA_KEY_FILE_ENV_VAR)
    if not sa_key_file:
        logger.error(f"Missing {GOOGLE_SA_KEY_FILE_ENV_VAR} environment variable")
        raise HTTPException(status_code=500, detail=MISSING_SA_CONFIG_ERROR)
    
    try:
        # Create credentials from service account file
        creds = service_account.Credentials.from_service_account_file(
            sa_key_file, scopes=scopes
        )
        
        # Build and cache the service
        service = build(service_name, version, credentials=creds)
        _services_cache[cache_key] = service
        return service
        
    except FileNotFoundError:
        logger.error(f"Service account key file not found: {sa_key_file}")
        raise HTTPException(status_code=500, detail=MISSING_SA_CONFIG_ERROR)
    except Exception as e:
        logger.error(f"Error creating Google {service_name} service: {str(e)}")
        raise HTTPException(status_code=500, detail=f"{GOOGLE_API_ERROR}: {str(e)}")

def verify_api_key(authorization: Optional[str] = Header(None)):
    """
    Verify the API key from the Authorization header.
    To be used with FastAPI Depends.
    
    Args:
        authorization: The Authorization header value
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not authorization:
        raise HTTPException(status_code=401, detail=MISSING_API_KEY_ERROR)
    
    # Extract Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail=INVALID_API_KEY_ERROR)
    
    token = parts[1]
    expected_api_key = os.getenv(API_KEY_ENV_VAR, DEFAULT_API_KEY)
    
    if not expected_api_key:
        logger.error(f"Missing {API_KEY_ENV_VAR} environment variable")
        raise HTTPException(status_code=500, detail="API key configuration error")
    
    if token != expected_api_key:
        raise HTTPException(status_code=401, detail=INVALID_API_KEY_ERROR)
    
    return token

def require_api_key(func: Callable) -> Callable:
    """
    Decorator to require API key for endpoints.
    Kept for backward compatibility.
    
    Args:
        func: The endpoint function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            raise HTTPException(status_code=401, detail=MISSING_API_KEY_ERROR)
        
        # Extract Bearer token
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail=INVALID_API_KEY_ERROR)
        
        token = parts[1]
        expected_api_key = os.getenv(API_KEY_ENV_VAR, DEFAULT_API_KEY)
        
        if not expected_api_key:
            logger.error(f"Missing {API_KEY_ENV_VAR} environment variable")
            raise HTTPException(status_code=500, detail="API key configuration error")
        
        if token != expected_api_key:
            raise HTTPException(status_code=401, detail=INVALID_API_KEY_ERROR)
        
        return await func(request, *args, **kwargs)
    
    return wrapper

def handle_google_api_error(func: Callable) -> Callable:
    """
    Decorator to handle Google API errors gracefully.
    
    Args:
        func: The endpoint function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HttpError as error:
            error_details = json.loads(error.content.decode())
            error_message = error_details.get("error", {}).get("message", str(error))
            status_code = error.resp.status
            
            logger.error(f"Google API error: {error_message}")
            raise HTTPException(status_code=status_code, detail=f"{GOOGLE_API_ERROR}: {error_message}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
    
    return wrapper

async def resolve_path(service, path: str, create_missing: bool = False):
    """
    Resolve a path like '/Folder1/Folder2/File' to the file ID.
    Optionally create missing folders in the path.
    
    Args:
        service: Google Drive service
        path: Path string with folder names separated by '/'
        create_missing: Whether to create missing folders
        
    Returns:
        Tuple of (file_id, parent_id, is_folder)
        
    Raises:
        HTTPException: If path resolution fails
    """
    parts = [p for p in path.split('/') if p]
    
    if not parts:
        # Return root folder
        return 'root', None, True
    
    parent_id = 'root'
    current_id = None
    
    # Traverse the path
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        query = f"name = '{part}' and '{parent_id}' in parents and trashed = false"
        
        # Search for the current part in the parent folder
        response = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, mimeType)',
        ).execute()
        
        items = response.get('files', [])
        
        if items:
            # Item exists
            current_id = items[0]['id']
            is_folder = items[0]['mimeType'] == 'application/vnd.google-apps.folder'
            
            # If not the last part, it must be a folder
            if not is_last and not is_folder:
                raise HTTPException(status_code=400, detail=f"'{part}' is not a folder")
                
            parent_id = current_id
        elif create_missing:
            # Create missing folder
            folder_metadata = {
                'name': part,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            current_id = folder['id']
            parent_id = current_id
            is_folder = True
        else:
            # Item doesn't exist and we're not creating it
            raise HTTPException(status_code=404, detail=f"Path component '{part}' not found")
    
    return current_id, parent_id, is_folder
