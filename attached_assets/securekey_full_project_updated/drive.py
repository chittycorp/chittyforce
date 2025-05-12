from fastapi import APIRouter, Request
from utils import get_drive_service, require_api_key

router = APIRouter()

@router.post("/drive/folder/create")
@require_api_key
def create_folder(request: Request, name: str, parent_id: str = None):
    service = get_drive_service()
    folder_metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        folder_metadata['parents'] = [parent_id]
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return {"folder_id": folder["id"]}
