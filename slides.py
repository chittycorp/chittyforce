from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from utils import get_drive_service, get_slides_service, verify_api_key, handle_google_api_error, resolve_path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Models
class SlideCreateRequest(BaseModel):
    title: str
    parent_id: Optional[str] = Field(None, description="Parent folder ID. Uses root if not specified.")

class SlidePathCreateRequest(BaseModel):
    path: str = Field(..., description="Path like '/Folder1/Folder2/Presentation'")
    create_missing_folders: bool = Field(True, description="Create missing folders in the path")

class SlideElement(BaseModel):
    object_id: Optional[str] = Field(None, description="Optional ID for the element")
    
class TextElement(SlideElement):
    text: str = Field(..., description="Text content")
    position: Dict[str, float] = Field(..., description="Position (x,y) in points")
    size: Dict[str, float] = Field(..., description="Size (width, height) in points")
    style: Optional[Dict[str, Any]] = Field(None, description="Text style properties")

class ImageElement(SlideElement):
    url: str = Field(..., description="Image URL")
    position: Dict[str, float] = Field(..., description="Position (x,y) in points")
    size: Dict[str, float] = Field(..., description="Size (width, height) in points")

class ShapeElement(SlideElement):
    shape_type: str = Field(..., description="Shape type (RECTANGLE, ELLIPSE, etc.)")
    position: Dict[str, float] = Field(..., description="Position (x,y) in points")
    size: Dict[str, float] = Field(..., description="Size (width, height) in points")
    style: Optional[Dict[str, Any]] = Field(None, description="Shape style properties")

class AddSlideRequest(BaseModel):
    presentation_id: str
    elements: Optional[List[Union[TextElement, ImageElement, ShapeElement]]] = Field(None, description="Elements to add to the slide")
    
class UpdateSlideRequest(BaseModel):
    presentation_id: str
    slide_id: str
    elements: List[Union[TextElement, ImageElement, ShapeElement]]

class Response(BaseModel):
    success: bool
    data: dict

# Endpoints
@router.post("/slides/create", response_model=Response)
@handle_google_api_error
async def create_presentation(
    request: SlideCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new Google Slides presentation"""
    drive_service = get_drive_service()
    
    # Create presentation in Drive
    presentation_metadata = {
        "name": request.title,
        "mimeType": "application/vnd.google-apps.presentation"
    }
    
    if request.parent_id:
        presentation_metadata["parents"] = [request.parent_id]
    
    presentation = drive_service.files().create(
        body=presentation_metadata,
        fields="id,name,webViewLink"
    ).execute()
    
    return {
        "success": True,
        "data": {
            "presentation_id": presentation["id"],
            "title": presentation["name"],
            "web_view_link": presentation.get("webViewLink")
        }
    }

@router.post("/slides/create-at-path", response_model=Response)
@handle_google_api_error
async def create_presentation_at_path(
    request: SlidePathCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a new Google Slides presentation at a specified path"""
    drive_service = get_drive_service()
    
    # Split path into parent path and presentation name
    parts = [p for p in request.path.split('/') if p]
    if not parts:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    presentation_name = parts[-1]
    parent_path = '/' + '/'.join(parts[:-1]) if len(parts) > 1 else '/'
    
    # Resolve parent path
    parent_id, _, is_folder = await resolve_path(
        drive_service, 
        parent_path, 
        request.create_missing_folders
    )
    
    if not is_folder:
        raise HTTPException(status_code=400, detail="Parent path is not a folder")
    
    # Create presentation in the resolved folder
    presentation_metadata = {
        "name": presentation_name,
        "mimeType": "application/vnd.google-apps.presentation",
        "parents": [parent_id]
    }
    
    presentation = drive_service.files().create(
        body=presentation_metadata,
        fields="id,name,webViewLink"
    ).execute()
    
    return {
        "success": True,
        "data": {
            "presentation_id": presentation["id"],
            "title": presentation["name"],
            "web_view_link": presentation.get("webViewLink"),
            "parent_id": parent_id,
            "path": request.path
        }
    }

@router.post("/slides/add", response_model=Response)
@handle_google_api_error
async def add_slide(
    request: AddSlideRequest,
    api_key: str = Depends(verify_api_key)
):
    """Add a new slide to a presentation with optional elements"""
    slides_service = get_slides_service()
    
    # Start with creating a new slide
    requests = [
        {
            "createSlide": {
                "slideLayoutReference": {
                    "predefinedLayout": "BLANK"
                }
            }
        }
    ]
    
    # Execute the slide creation request first to get the slide ID
    result = slides_service.presentations().batchUpdate(
        presentationId=request.presentation_id,
        body={"requests": requests}
    ).execute()
    
    # Get the new slide ID
    slide_id = result.get("replies", [{}])[0].get("createSlide", {}).get("objectId")
    
    # If there are elements to add, prepare a new batch update
    element_requests = []
    if request.elements:
        for element in request.elements:
            if isinstance(element, TextElement):
                # Add text box
                element_id = element.object_id or f"text_{slide_id}_{len(element_requests)}"
                element_requests.append({
                    "createShape": {
                        "objectId": element_id,
                        "shapeType": "TEXT_BOX",
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {
                                "width": {"magnitude": element.size["width"], "unit": "PT"},
                                "height": {"magnitude": element.size["height"], "unit": "PT"}
                            },
                            "transform": {
                                "scaleX": 1,
                                "scaleY": 1,
                                "translateX": element.position["x"],
                                "translateY": element.position["y"],
                                "unit": "PT"
                            }
                        }
                    }
                })
                
                # Insert text into the text box
                element_requests.append({
                    "insertText": {
                        "objectId": element_id,
                        "insertionIndex": 0,
                        "text": element.text
                    }
                })
                
                # Apply style if specified
                if element.style:
                    style_request = {
                        "updateTextStyle": {
                            "objectId": element_id,
                            "textRange": {
                                "type": "ALL"
                            },
                            "style": element.style,
                            "fields": ",".join(element.style.keys())
                        }
                    }
                    element_requests.append(style_request)
                    
            elif isinstance(element, ImageElement):
                # Add image
                element_id = element.object_id or f"image_{slide_id}_{len(element_requests)}"
                element_requests.append({
                    "createImage": {
                        "objectId": element_id,
                        "url": element.url,
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {
                                "width": {"magnitude": element.size["width"], "unit": "PT"},
                                "height": {"magnitude": element.size["height"], "unit": "PT"}
                            },
                            "transform": {
                                "scaleX": 1,
                                "scaleY": 1,
                                "translateX": element.position["x"],
                                "translateY": element.position["y"],
                                "unit": "PT"
                            }
                        }
                    }
                })
                
            elif isinstance(element, ShapeElement):
                # Add shape
                element_id = element.object_id or f"shape_{slide_id}_{len(element_requests)}"
                element_requests.append({
                    "createShape": {
                        "objectId": element_id,
                        "shapeType": element.shape_type,
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {
                                "width": {"magnitude": element.size["width"], "unit": "PT"},
                                "height": {"magnitude": element.size["height"], "unit": "PT"}
                            },
                            "transform": {
                                "scaleX": 1,
                                "scaleY": 1,
                                "translateX": element.position["x"],
                                "translateY": element.position["y"],
                                "unit": "PT"
                            }
                        }
                    }
                })
                
                # Apply style if specified
                if element.style:
                    style_request = {
                        "updateShapeProperties": {
                            "objectId": element_id,
                            "shapeProperties": {
                                "shapeBackgroundFill": element.style.get("backgroundFill"),
                                "outline": element.style.get("outline")
                            },
                            "fields": ",".join([f"shapeBackgroundFill" if "backgroundFill" in element.style else "", 
                                               f"outline" if "outline" in element.style else ""]).strip(",")
                        }
                    }
                    element_requests.append(style_request)
    
    # Execute element creation if there are any
    if element_requests:
        slides_service.presentations().batchUpdate(
            presentationId=request.presentation_id,
            body={"requests": element_requests}
        ).execute()
    
    return {
        "success": True,
        "data": {
            "presentation_id": request.presentation_id,
            "slide_id": slide_id,
            "elements_added": len(request.elements) if request.elements else 0
        }
    }

@router.get("/slides/{presentation_id}", response_model=Response)
@handle_google_api_error
async def get_presentation(
    presentation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get metadata about a presentation"""
    slides_service = get_slides_service()
    
    presentation = slides_service.presentations().get(
        presentationId=presentation_id
    ).execute()
    
    # Extract slide information
    slides = []
    for slide in presentation.get("slides", []):
        slide_info = {
            "slide_id": slide.get("objectId"),
            "elements": len(slide.get("pageElements", [])),
            "slide_number": slide.get("slideProperties", {}).get("layoutProperties", {}).get("displayName", "")
        }
        slides.append(slide_info)
    
    return {
        "success": True,
        "data": {
            "presentation_id": presentation.get("presentationId"),
            "title": presentation.get("title"),
            "slides": slides,
            "slide_count": len(slides)
        }
    }

@router.delete("/slides/{presentation_id}/slides/{slide_id}", response_model=Response)
@handle_google_api_error
async def delete_slide(
    presentation_id: str,
    slide_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Delete a slide from a presentation"""
    slides_service = get_slides_service()
    
    result = slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": [
                {
                    "deleteObject": {
                        "objectId": slide_id
                    }
                }
            ]
        }
    ).execute()
    
    return {
        "success": True,
        "data": {
            "presentation_id": presentation_id,
            "deleted_slide_id": slide_id
        }
    }

@router.post("/slides/{presentation_id}/refresh-theme", response_model=Response)
@handle_google_api_error
async def refresh_theme(
    presentation_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Refresh the theme of a presentation"""
    slides_service = get_slides_service()
    
    # First, get the current theme ID
    presentation = slides_service.presentations().get(
        presentationId=presentation_id,
        fields="layouts"
    ).execute()
    
    # Create a refresh theme request
    result = slides_service.presentations().batchUpdate(
        presentationId=presentation_id,
        body={
            "requests": [
                {
                    "refreshTheme": {}
                }
            ]
        }
    ).execute()
    
    return {
        "success": True,
        "data": {
            "presentation_id": presentation_id,
            "message": "Theme refreshed successfully"
        }
    }
