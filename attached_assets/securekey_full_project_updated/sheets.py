from fastapi import APIRouter, Request
from utils import get_drive_service, require_api_key

router = APIRouter()

@router.post("/sheet/create")
@require_api_key
def create_sheet(request: Request, title: str):
    service = get_drive_service()
    sheet = service.files().create(
        body={"name": title, "mimeType": "application/vnd.google-apps.spreadsheet"}
    ).execute()
    return {"spreadsheet_id": sheet["id"]}
