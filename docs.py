from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from utils import get_drive_service, get_docs_service, verify_api_key, handle_google_api_error, resolve_path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Models
class DocCreateRequest(BaseModel):
    title: str
    parent_id: Optional[str] = Field(None, description="Parent folder ID. Uses root if not specified.")
    content: Optional[str] = Field(None, description="Initial content for the document")

class DocPathCreateRequest(BaseModel):
    path: str = Field(..., description="Path like '/Folder1/Folder2/Document'")
    content: Optional[str] = Field(None, description="Initial content for the document")
    create_missing_folders: bool = Field(True, description="Create missing folders in the path")

class DocContentRequest(BaseModel):
    document_id: str
    content: str = Field(..., description="Content to append or replace")

class DocReplaceContentRequest(BaseModel):
    document_id: str
    content: str = Field(..., description="Content to replace entire document with")

class ParagraphStyle(BaseModel):
    named_style_type: Optional[str] = Field(None, description="Named style like HEADING_1, NORMAL_TEXT, etc.")
    alignment: Optional[str] = Field(None, description="Alignment: START, CENTER, END, JUSTIFIED")

class TextStyle(BaseModel):
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    underline: Optional[bool] = None
    font_size: Optional[int] = Field(None, description="Font size in points")
    foreground_color: Optional[Dict[str, float]] = Field(None, description="RGB color with values 0-1")

class InsertTextRequest(BaseModel):
    document_id: str
    text: str = Field(..., description="Text to insert")
    index: int = Field(..., description="Index where to insert the text")
    paragraph_style: Optional[ParagraphStyle] = None
    text_style: Optional[TextStyle] = None

class Response(BaseModel):
    success: bool
    data: dict

# Endpoints
@router.post("/docs/create", response_model=Response)
@handle_google_api_error
async def create_doc(
    request: DocCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new Google Docs document"""
    drive_service = get_drive_service()
    docs_service = get_docs_service()
    
    # Create document in Drive
    doc_metadata = {
        "name": request.title,
        "mimeType": "application/vnd.google-apps.document"
    }
    
    if request.parent_id:
        doc_metadata["parents"] = [request.parent_id]
    
    doc = drive_service.files().create(
        body=doc_metadata,
        fields="id,name,webViewLink"
    ).execute()
    
    # Add initial content if provided
    if request.content:
        docs_service.documents().batchUpdate(
            documentId=doc["id"],
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {
                                "index": 1
                            },
                            "text": request.content
                        }
                    }
                ]
            }
        ).execute()
    
    return {
        "success": True,
        "data": {
            "document_id": doc["id"],
            "title": doc["name"],
            "web_view_link": doc.get("webViewLink")
        }
    }

@router.post("/docs/create-at-path", response_model=Response)
@handle_google_api_error
async def create_doc_at_path(
    request: DocPathCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new Google Docs document at a specified path"""
    drive_service = get_drive_service()
    docs_service = get_docs_service()
    
    # Split path into parent path and document name
    parts = [p for p in request.path.split('/') if p]
    if not parts:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    doc_name = parts[-1]
    parent_path = '/' + '/'.join(parts[:-1]) if len(parts) > 1 else '/'
    
    # Resolve parent path
    parent_id, _, is_folder = await resolve_path(
        drive_service, 
        parent_path, 
        request.create_missing_folders
    )
    
    if not is_folder:
        raise HTTPException(status_code=400, detail="Parent path is not a folder")
    
    # Create document in the resolved folder
    doc_metadata = {
        "name": doc_name,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [parent_id]
    }
    
    doc = drive_service.files().create(
        body=doc_metadata,
        fields="id,name,webViewLink"
    ).execute()
    
    # Add initial content if provided
    if request.content:
        docs_service.documents().batchUpdate(
            documentId=doc["id"],
            body={
                "requests": [
                    {
                        "insertText": {
                            "location": {
                                "index": 1
                            },
                            "text": request.content
                        }
                    }
                ]
            }
        ).execute()
    
    return {
        "success": True,
        "data": {
            "document_id": doc["id"],
            "title": doc["name"],
            "web_view_link": doc.get("webViewLink"),
            "parent_id": parent_id,
            "path": request.path
        }
    }

@router.post("/docs/append", response_model=Response)
@handle_google_api_error
async def append_to_doc(
    request: DocContentRequest,
    api_key: str = Depends(verify_api_key)
):
    """Append content to the end of a Google Docs document"""
    docs_service = get_docs_service()
    
    # Get document to find the end index
    document = docs_service.documents().get(documentId=request.document_id).execute()
    end_index = document.get('body', {}).get('content', [])[-1].get('endIndex', 1)
    
    # Append text at the end
    result = docs_service.documents().batchUpdate(
        documentId=request.document_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {
                            "index": end_index - 1
                        },
                        "text": request.content
                    }
                }
            ]
        }
    ).execute()
    
    return {
        "success": True,
        "data": {
            "document_id": request.document_id,
            "appended_content_length": len(request.content)
        }
    }

@router.post("/docs/replace", response_model=Response)
@handle_google_api_error
async def replace_doc_content(
    request: DocReplaceContentRequest,
    api_key: str = Depends(verify_api_key)
):
    """Replace the entire content of a Google Docs document"""
    docs_service = get_docs_service()
    
    # Get document to find content range
    document = docs_service.documents().get(documentId=request.document_id).execute()
    end_index = document.get('body', {}).get('content', [])[-1].get('endIndex', 1)
    
    # Delete all content and insert new content
    result = docs_service.documents().batchUpdate(
        documentId=request.document_id,
        body={
            "requests": [
                {
                    "deleteContentRange": {
                        "range": {
                            "startIndex": 1,
                            "endIndex": end_index - 1
                        }
                    }
                },
                {
                    "insertText": {
                        "location": {
                            "index": 1
                        },
                        "text": request.content
                    }
                }
            ]
        }
    ).execute()
    
    return {
        "success": True,
        "data": {
            "document_id": request.document_id,
            "content_length": len(request.content)
        }
    }

@router.post("/docs/insert", response_model=Response)
@handle_google_api_error
async def insert_text(
    request: InsertTextRequest,
    api_key: str = Depends(verify_api_key)
):
    """Insert text at a specific position in a Google Docs document with optional styling"""
    docs_service = get_docs_service()
    
    # Prepare the insert request
    batch_requests = [
        {
            "insertText": {
                "location": {
                    "index": request.index
                },
                "text": request.text
            }
        }
    ]
    
    # Add styling if specified
    if request.paragraph_style or request.text_style:
        style_request = {
            "updateTextStyle": {
                "range": {
                    "startIndex": request.index,
                    "endIndex": request.index + len(request.text)
                },
                "textStyle": {},
                "fields": ""
            }
        }
        
        fields = []
        
        if request.text_style:
            text_style = {}
            for attr, value in request.text_style.dict(exclude_none=True).items():
                if attr == "font_size":
                    text_style["fontSize"] = {"magnitude": value, "unit": "PT"}
                    fields.append("fontSize")
                elif attr == "foreground_color":
                    text_style["foregroundColor"] = value
                    fields.append("foregroundColor")
                else:
                    text_style[attr] = value
                    fields.append(attr)
            
            style_request["updateTextStyle"]["textStyle"] = text_style
            style_request["updateTextStyle"]["fields"] = ",".join(fields)
            batch_requests.append(style_request)
        
        if request.paragraph_style:
            paragraph_style = {}
            paragraph_fields = []
            
            paragraph_dict = request.paragraph_style.dict(exclude_none=True)
            if paragraph_dict:
                for attr, value in paragraph_dict.items():
                    if attr == "named_style_type":
                        paragraph_style["namedStyleType"] = value
                        paragraph_fields.append("namedStyleType")
                    else:
                        paragraph_style[attr] = value
                        paragraph_fields.append(attr)
                
                batch_requests.append({
                    "updateParagraphStyle": {
                        "range": {
                            "startIndex": request.index,
                            "endIndex": request.index + len(request.text)
                        },
                        "paragraphStyle": paragraph_style,
                        "fields": ",".join(paragraph_fields)
                    }
                })
    
    # Execute the batch update
    result = docs_service.documents().batchUpdate(
        documentId=request.document_id,
        body={"requests": batch_requests}
    ).execute()
    
    return {
        "success": True,
        "data": {
            "document_id": request.document_id,
            "inserted_text_length": len(request.text),
            "insert_index": request.index
        }
    }

@router.get("/docs/{document_id}", response_model=Response)
@handle_google_api_error
async def get_doc_content(
    document_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get the content of a Google Docs document"""
    docs_service = get_docs_service()
    
    document = docs_service.documents().get(documentId=document_id).execute()
    
    # Extract text content from the document
    text_content = ""
    for element in document.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for paragraph_element in element.get('paragraph', {}).get('elements', []):
                if 'textRun' in paragraph_element:
                    text_content += paragraph_element.get('textRun', {}).get('content', '')
    
    return {
        "success": True,
        "data": {
            "document_id": document_id,
            "title": document.get('title', ''),
            "content": text_content,
            "document_metadata": {
                "revision_id": document.get('revisionId'),
                "document_id": document.get('documentId')
            }
        }
    }
