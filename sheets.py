from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from utils import get_drive_service, get_sheets_service, verify_api_key, handle_google_api_error, resolve_path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Models
class SheetCreateRequest(BaseModel):
    title: str
    parent_id: Optional[str] = Field(None, description="Parent folder ID. Uses root if not specified.")
    
class SheetPathCreateRequest(BaseModel):
    path: str = Field(..., description="Path like '/Folder1/Folder2/Spreadsheet'")
    create_missing_folders: bool = Field(True, description="Create missing folders in the path")

class ValueRange(BaseModel):
    range: str = Field(..., description="A1 notation range")
    values: List[List[Any]] = Field(..., description="Values to write")
    
class BatchUpdateRequest(BaseModel):
    spreadsheet_id: str
    data: List[ValueRange]
    value_input_option: str = Field("USER_ENTERED", description="How input data should be interpreted")

class AddSheetRequest(BaseModel):
    spreadsheet_id: str
    title: str = Field(..., description="Title of the new sheet")
    
class FormatCellRequest(BaseModel):
    spreadsheet_id: str
    range: str = Field(..., description="A1 notation range")
    format: Dict[str, Any] = Field(..., description="Cell format specification")

class Response(BaseModel):
    success: bool
    data: dict

# Endpoints
@router.post("/sheets/create", response_model=Response)
@handle_google_api_error
async def create_sheet(
    request: SheetCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new Google Sheets spreadsheet"""
    drive_service = get_drive_service()
    
    # Create spreadsheet in Drive
    sheet_metadata = {
        "name": request.title,
        "mimeType": "application/vnd.google-apps.spreadsheet"
    }
    
    if request.parent_id:
        sheet_metadata["parents"] = [request.parent_id]
    
    sheet = drive_service.files().create(
        body=sheet_metadata,
        fields="id,name,webViewLink"
    ).execute()
    
    return {
        "success": True,
        "data": {
            "spreadsheet_id": sheet["id"],
            "title": sheet["name"],
            "web_view_link": sheet.get("webViewLink")
        }
    }

@router.post("/sheets/create-at-path", response_model=Response)
@handle_google_api_error
async def create_sheet_at_path(
    request: SheetPathCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new Google Sheets spreadsheet at a specified path"""
    drive_service = get_drive_service()
    
    # Split path into parent path and spreadsheet name
    parts = [p for p in request.path.split('/') if p]
    if not parts:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    sheet_name = parts[-1]
    parent_path = '/' + '/'.join(parts[:-1]) if len(parts) > 1 else '/'
    
    # Resolve parent path
    parent_id, _, is_folder = await resolve_path(
        drive_service, 
        parent_path, 
        request.create_missing_folders
    )
    
    if not is_folder:
        raise HTTPException(status_code=400, detail="Parent path is not a folder")
    
    # Create spreadsheet in the resolved folder
    sheet_metadata = {
        "name": sheet_name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
        "parents": [parent_id]
    }
    
    sheet = drive_service.files().create(
        body=sheet_metadata,
        fields="id,name,webViewLink"
    ).execute()
    
    return {
        "success": True,
        "data": {
            "spreadsheet_id": sheet["id"],
            "title": sheet["name"],
            "web_view_link": sheet.get("webViewLink"),
            "parent_id": parent_id,
            "path": request.path
        }
    }

@router.post("/sheets/values", response_model=Response)
@handle_google_api_error
async def update_values(
    request: BatchUpdateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update values in a spreadsheet"""
    sheets_service = get_sheets_service()
    
    # Prepare batch update request
    batch_data = []
    for item in request.data:
        batch_data.append({
            "range": item.range,
            "values": item.values
        })
    
    result = sheets_service.spreadsheets().values().batchUpdate(
        spreadsheetId=request.spreadsheet_id,
        body={
            "valueInputOption": request.value_input_option,
            "data": batch_data
        }
    ).execute()
    
    return {
        "success": True,
        "data": {
            "spreadsheet_id": request.spreadsheet_id,
            "updated_cells": result.get("totalUpdatedCells"),
            "updated_ranges": result.get("totalUpdatedRanges")
        }
    }

@router.get("/sheets/{spreadsheet_id}/values/{range}", response_model=Response)
@handle_google_api_error
async def get_values(
    spreadsheet_id: str,
    range: str,
    value_render_option: str = Query("FORMATTED_VALUE", description="How values should be rendered"),
    api_key: str = Depends(verify_api_key)
):
    """Get values from a spreadsheet range"""
    sheets_service = get_sheets_service()
    
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range,
        valueRenderOption=value_render_option
    ).execute()
    
    return {
        "success": True,
        "data": {
            "range": result.get("range"),
            "values": result.get("values", [])
        }
    }

@router.post("/sheets/add-sheet", response_model=Response)
@handle_google_api_error
async def add_sheet(
    request: AddSheetRequest,
    api_key: str = Depends(verify_api_key)
):
    """Add a new sheet to an existing spreadsheet"""
    sheets_service = get_sheets_service()
    
    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=request.spreadsheet_id,
        body={
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": request.title
                        }
                    }
                }
            ]
        }
    ).execute()
    
    # Extract the new sheet information
    new_sheet = result.get("replies", [{}])[0].get("addSheet", {}).get("properties", {})
    
    return {
        "success": True,
        "data": {
            "spreadsheet_id": request.spreadsheet_id,
            "sheet_id": new_sheet.get("sheetId"),
            "title": new_sheet.get("title"),
            "index": new_sheet.get("index")
        }
    }

@router.get("/sheets/{spreadsheet_id}", response_model=Response)
@handle_google_api_error
async def get_spreadsheet_metadata(
    spreadsheet_id: str,
    include_grid_data: bool = Query(False, description="Whether to include grid data"),
    api_key: str = Depends(verify_api_key)
):
    """Get metadata about a spreadsheet"""
    sheets_service = get_sheets_service()
    
    fields = "spreadsheetId,properties,sheets.properties"
    if include_grid_data:
        fields += ",sheets.data"
    
    result = sheets_service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        includeGridData=include_grid_data,
        fields=fields
    ).execute()
    
    # Extract sheet information
    sheets = []
    for sheet in result.get("sheets", []):
        sheet_info = {
            "sheet_id": sheet.get("properties", {}).get("sheetId"),
            "title": sheet.get("properties", {}).get("title"),
            "index": sheet.get("properties", {}).get("index"),
            "grid_properties": sheet.get("properties", {}).get("gridProperties", {})
        }
        sheets.append(sheet_info)
    
    return {
        "success": True,
        "data": {
            "spreadsheet_id": result.get("spreadsheetId"),
            "title": result.get("properties", {}).get("title"),
            "sheets": sheets
        }
    }

@router.post("/sheets/format", response_model=Response)
@handle_google_api_error
async def format_cells(
    request: FormatCellRequest,
    api_key: str = Depends(verify_api_key)
):
    """Format cells in a spreadsheet"""
    sheets_service = get_sheets_service()
    
    # Extract grid range from A1 notation
    # This is a simplified approach - in a production app you'd need 
    # a more robust conversion from A1 to GridRange
    sheet_name = None
    if "!" in request.range:
        sheet_name, cell_range = request.range.split("!")
        if sheet_name.startswith("'") and sheet_name.endswith("'"):
            sheet_name = sheet_name[1:-1]
    else:
        cell_range = request.range
    
    # Get sheet ID first if sheet name is specified
    sheet_id = 0  # Default to first sheet
    if sheet_name:
        metadata = sheets_service.spreadsheets().get(
            spreadsheetId=request.spreadsheet_id,
            fields="sheets.properties"
        ).execute()
        
        for sheet in metadata.get("sheets", []):
            if sheet.get("properties", {}).get("title") == sheet_name:
                sheet_id = sheet.get("properties", {}).get("sheetId")
                break
    
    # Create format request
    result = sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=request.spreadsheet_id,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            # Note: This is a simplification 
                            # A production app should convert A1 notation to proper range
                        },
                        "cell": {
                            "userEnteredFormat": request.format
                        },
                        "fields": "userEnteredFormat"
                    }
                }
            ]
        }
    ).execute()
    
    return {
        "success": True,
        "data": {
            "spreadsheet_id": request.spreadsheet_id,
            "range": request.range,
            "applied_format": request.format
        }
    }
