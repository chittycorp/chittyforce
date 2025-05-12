from fastapi import APIRouter, Request
from utils import get_drive_service, require_api_key

router = APIRouter()

@router.post("/slides/create")
@require_api_key
def create_presentation(request: Request, title: str):
    service = get_drive_service()
    presentation = service.files().create(
        body={"name": title, "mimeType": "application/vnd.google-apps.presentation"}
    ).execute()
    return {"presentation_id": presentation["id"]}
