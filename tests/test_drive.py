import pytest
from fastapi.testclient import TestClient
import os
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

# Mock API key for tests
os.environ["API_KEY"] = "test_api_key"
AUTH_HEADERS = {"Authorization": "Bearer test_api_key"}

# Mock data
MOCK_FOLDER = {
    "id": "folder123",
    "name": "Test Folder",
    "mimeType": "application/vnd.google-apps.folder",
    "webViewLink": "https://drive.google.com/drive/folders/folder123"
}

MOCK_FILE = {
    "id": "file123",
    "name": "Test File",
    "mimeType": "application/vnd.google-docs.document",
    "webViewLink": "https://docs.google.com/document/d/file123"
}

MOCK_FILES_LIST = {
    "files": [
        MOCK_FILE,
        MOCK_FOLDER
    ],
    "nextPageToken": "token123"
}

# Test creating a folder
@patch("utils.get_drive_service")
def test_create_folder(mock_get_drive_service):
    # Setup mock
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_create = MagicMock()
    mock_create.return_value.execute.return_value = MOCK_FOLDER
    
    mock_files.create = mock_create
    mock_service.files.return_value = mock_files
    mock_get_drive_service.return_value = mock_service
    
    # Test API
    response = client.post(
        "/drive/folder/create",
        headers=AUTH_HEADERS,
        json={"name": "Test Folder"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["folder_id"] == "folder123"
    assert data["data"]["name"] == "Test Folder"
    
    # Verify mock was called correctly
    create_call = mock_create.call_args[1]
    assert create_call["body"]["name"] == "Test Folder"
    assert create_call["body"]["mimeType"] == "application/vnd.google-apps.folder"

# Test listing files
@patch("utils.get_drive_service")
def test_list_files(mock_get_drive_service):
    # Setup mock
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_list = MagicMock()
    mock_list.return_value.execute.return_value = MOCK_FILES_LIST
    
    mock_files.list = mock_list
    mock_service.files.return_value = mock_files
    mock_get_drive_service.return_value = mock_service
    
    # Test API
    response = client.get(
        "/drive/files?parent_id=parent123",
        headers=AUTH_HEADERS
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert len(data["data"]["files"]) == 2
    assert data["data"]["next_page_token"] == "token123"
    
    # Verify mock was called correctly
    list_call = mock_list.call_args[1]
    assert "parent123" in list_call["q"]
    assert "trashed = false" in list_call["q"]

# Test getting file metadata
@patch("utils.get_drive_service")
def test_get_file(mock_get_drive_service):
    # Setup mock
    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_get = MagicMock()
    mock_get.return_value.execute.return_value = MOCK_FILE
    
    mock_files.get = mock_get
    mock_service.files.return_value = mock_files
    mock_get_drive_service.return_value = mock_service
    
    # Test API
    response = client.get(
        "/drive/file/file123",
        headers=AUTH_HEADERS
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["id"] == "file123"
    assert data["data"]["name"] == "Test File"
    
    # Verify mock was called correctly
    get_call = mock_get.call_args[1]
    assert get_call["fileId"] == "file123"
