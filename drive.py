from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from utils import get_drive_service, verify_api_key, handle_google_api_error, resolve_path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Models
class FileMetadata(BaseModel):
    id: str
    name: str
    mimeType: str
    size: Optional[str] = None
    createdTime: Optional[str] = None
    modifiedTime: Optional[str] = None
    webViewLink: Optional[str] = None
    
class FolderRequest(BaseModel):
    name: str
    parent_id: Optional[str] = Field(None, description="Parent folder ID. Uses root if not specified.")
    
class FileRequest(BaseModel):
    name: str
    parent_id: Optional[str] = Field(None, description="Parent folder ID. Uses root if not specified.")
    mime_type: Optional[str] = Field(None, description="MIME type of the file")
    
class PathRequest(BaseModel):
    path: str = Field(..., description="Path like '/Folder1/Folder2/File'")
    create_missing: bool = Field(False, description="Create missing folders in the path")
    
class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    
class MoveRequest(BaseModel):
    file_id: str
    new_parent_id: str
    remove_parents: Optional[List[str]] = None

class RenameRequest(BaseModel):
    file_id: str
    new_name: str

class Response(BaseModel):
    success: bool
    data: dict

# Endpoints
@router.post("/drive/folder/create", response_model=Response)
@handle_google_api_error
async def create_folder(
    request: FolderRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new folder in Google Drive"""
    service = get_drive_service()
    
    folder_metadata = {
        'name': request.name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if request.parent_id:
        folder_metadata['parents'] = [request.parent_id]
    
    folder = service.files().create(
        body=folder_metadata,
        fields="id,name,mimeType,webViewLink"
    ).execute()
    
    return {
        "success": True,
        "data": {
            "folder_id": folder["id"],
            "name": folder["name"],
            "mime_type": folder["mimeType"],
            "web_view_link": folder.get("webViewLink")
        }
    }

@router.post("/drive/path/resolve", response_model=Response)
@handle_google_api_error
async def resolve_drive_path(
    request: PathRequest,
    api_key: str = Depends(verify_api_key)
):
    """Resolve a path to a file or folder ID, optionally creating missing folders"""
    service = get_drive_service()
    
    file_id, parent_id, is_folder = await resolve_path(
        service, 
        request.path, 
        request.create_missing
    )
    
    # Get file metadata
    file_metadata = service.files().get(
        fileId=file_id,
        fields="id,name,mimeType,size,createdTime,modifiedTime,webViewLink"
    ).execute()
    
    return {
        "success": True,
        "data": {
            "file_id": file_id,
            "parent_id": parent_id,
            "is_folder": is_folder,
            "metadata": file_metadata
        }
    }

@router.get("/drive/files", response_model=Response)
@handle_google_api_error
async def list_files(
    parent_id: Optional[str] = Query(None, description="Parent folder ID. Uses root if not specified."),
    page_size: int = Query(100, description="Maximum number of files to return"),
    page_token: Optional[str] = Query(None, description="Page token for pagination"),
    order_by: str = Query("modifiedTime desc", description="Field to sort by"),
    api_key: str = Depends(verify_api_key)
):
    """List files in a folder"""
    service = get_drive_service()
    
    # Build query
    query = "trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    response = service.files().list(
        q=query,
        pageSize=page_size,
        fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
        pageToken=page_token,
        orderBy=order_by
    ).execute()
    
    files = response.get('files', [])
    next_page_token = response.get('nextPageToken')
    
    return {
        "success": True,
        "data": {
            "files": files,
            "next_page_token": next_page_token
        }
    }

@router.post("/drive/search", response_model=Response)
@handle_google_api_error
async def search_files(
    request: SearchRequest,
    page_size: int = Query(100, description="Maximum number of files to return"),
    page_token: Optional[str] = Query(None, description="Page token for pagination"),
    api_key: str = Depends(verify_api_key)
):
    """Search for files and folders in Google Drive"""
    service = get_drive_service()
    
    # Add non-trashed filter to query
    query = f"{request.query} and trashed = false"
    
    response = service.files().list(
        q=query,
        pageSize=page_size,
        fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
        pageToken=page_token
    ).execute()
    
    files = response.get('files', [])
    next_page_token = response.get('nextPageToken')
    
    return {
        "success": True,
        "data": {
            "files": files,
            "next_page_token": next_page_token
        }
    }

@router.post("/drive/file/move", response_model=Response)
@handle_google_api_error
async def move_file(
    request: MoveRequest,
    api_key: str = Depends(verify_api_key)
):
    """Move a file to a new folder"""
    service = get_drive_service()
    
    # Build parameters
    params = {
        'fileId': request.file_id,
        'addParents': request.new_parent_id,
        'fields': 'id,name,parents'
    }
    
    # Add removeParents if specified
    if request.remove_parents:
        params['removeParents'] = ','.join(request.remove_parents)
    
    updated_file = service.files().update(**params).execute()
    
    return {
        "success": True,
        "data": {
            "file_id": updated_file["id"],
            "name": updated_file["name"],
            "parents": updated_file.get("parents", [])
        }
    }

@router.post("/drive/file/rename", response_model=Response)
@handle_google_api_error
async def rename_file(
    request: RenameRequest,
    api_key: str = Depends(verify_api_key)
):
    """Rename a file or folder"""
    service = get_drive_service()
    
    updated_file = service.files().update(
        fileId=request.file_id,
        body={'name': request.new_name},
        fields='id,name'
    ).execute()
    
    return {
        "success": True,
        "data": {
            "file_id": updated_file["id"],
            "name": updated_file["name"]
        }
    }

@router.delete("/drive/file/{file_id}", response_model=Response)
@handle_google_api_error
async def delete_file(
    file_id: str,
    permanent: bool = Query(False, description="Permanently delete the file instead of trashing it"),
    api_key: str = Depends(verify_api_key)
):
    """Delete or trash a file or folder"""
    service = get_drive_service()
    
    if permanent:
        service.files().delete(fileId=file_id).execute()
    else:
        service.files().update(
            fileId=file_id,
            body={'trashed': True}
        ).execute()
    
    return {
        "success": True,
        "data": {
            "file_id": file_id,
            "permanent_delete": permanent
        }
    }

@router.get("/drive/file/{file_id}", response_model=Response)
@handle_google_api_error
async def get_file(
    file_id: str,
    fields: str = Query("id,name,mimeType,size,createdTime,modifiedTime,webViewLink,parents", 
                        description="Comma-separated list of fields to include"),
    api_key: str = Depends(verify_api_key)
):
    """Get metadata for a file or folder"""
    service = get_drive_service()
    
    file_metadata = service.files().get(
        fileId=file_id,
        fields=fields
    ).execute()
    
    return {
        "success": True,
        "data": file_metadata
    }
