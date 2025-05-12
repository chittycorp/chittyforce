from fastapi import APIRouter, Request
from utils import get_drive_service, require_api_key

router = APIRouter()

@router.post("/docs/create")
@require_api_key
def create_doc(request: Request, title: str):
    service = get_drive_service()
    doc = service.files().create(
        body={"name": title, "mimeType": "application/vnd.google-apps.document"}
    ).execute()
    return {"document_id": doc["id"]}
