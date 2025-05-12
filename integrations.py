from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from utils import verify_api_key, handle_google_api_error
import os
import logging
import json

# Optional imports for Notion and GitHub integration
try:
    from notion_client import Client as NotionClient
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

# Constants
NOTION_API_KEY_ENV = "NOTION_API_KEY"
GITHUB_API_KEY_ENV = "GITHUB_API_KEY"

# Models
class NotionPageCreateRequest(BaseModel):
    database_id: str = Field(..., description="Notion database ID")
    title: str = Field(..., description="Page title")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties for the page")

class NotionPageUpdateRequest(BaseModel):
    page_id: str = Field(..., description="Notion page ID")
    properties: Dict[str, Any] = Field(..., description="Properties to update")

class GitHubIssueCreateRequest(BaseModel):
    repo: str = Field(..., description="Repository in format 'owner/repo'")
    title: str = Field(..., description="Issue title")
    body: str = Field(..., description="Issue body")
    labels: Optional[List[str]] = Field(None, description="Issue labels")
    assignees: Optional[List[str]] = Field(None, description="Users to assign")

class GitHubProjectCardRequest(BaseModel):
    repo: str = Field(..., description="Repository in format 'owner/repo'")
    project_id: int = Field(..., description="Project ID")
    issue_id: int = Field(..., description="Issue ID to add to project")

class Response(BaseModel):
    success: bool
    data: dict

# Dependency Injection
def get_notion_client():
    """Get Notion client if available"""
    if not NOTION_AVAILABLE:
        raise HTTPException(status_code=501, detail="Notion integration not available. Install notion_client package.")
    
    api_key = os.getenv(NOTION_API_KEY_ENV)
    if not api_key:
        raise HTTPException(status_code=500, detail=f"Missing {NOTION_API_KEY_ENV} environment variable")
    
    return NotionClient(auth=api_key)

def get_github_client():
    """Get GitHub client if available"""
    if not GITHUB_AVAILABLE:
        raise HTTPException(status_code=501, detail="GitHub integration not available. Install PyGithub package.")
    
    api_key = os.getenv(GITHUB_API_KEY_ENV)
    if not api_key:
        raise HTTPException(status_code=500, detail=f"Missing {GITHUB_API_KEY_ENV} environment variable")
    
    return Github(api_key)

# Endpoints - Notion Integration
@router.post("/integrations/notion/page/create", response_model=Response)
@handle_google_api_error
async def create_notion_page(
    request: NotionPageCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create a page in a Notion database"""
    notion = get_notion_client()
    
    # Prepare properties with title
    if "Name" not in request.properties and "Title" not in request.properties:
        properties = {
            "Name": {"title": [{"text": {"content": request.title}}]},
            **request.properties
        }
    else:
        properties = request.properties
    
    # Create the page
    try:
        new_page = notion.pages.create(
            parent={"database_id": request.database_id},
            properties=properties
        )
        
        return {
            "success": True,
            "data": {
                "page_id": new_page["id"],
                "url": new_page.get("url")
            }
        }
    except Exception as e:
        logger.error(f"Notion API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Notion API error: {str(e)}")

@router.patch("/integrations/notion/page/{page_id}", response_model=Response)
@handle_google_api_error
async def update_notion_page(
    page_id: str,
    request: NotionPageUpdateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Update properties of a Notion page"""
    notion = get_notion_client()
    
    try:
        updated_page = notion.pages.update(
            page_id=page_id,
            properties=request.properties
        )
        
        return {
            "success": True,
            "data": {
                "page_id": updated_page["id"],
                "url": updated_page.get("url")
            }
        }
    except Exception as e:
        logger.error(f"Notion API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Notion API error: {str(e)}")

@router.get("/integrations/notion/database/{database_id}", response_model=Response)
@handle_google_api_error
async def query_notion_database(
    database_id: str,
    filter_json: Optional[str] = Query(None, description="JSON string of Notion filter object"),
    sorts_json: Optional[str] = Query(None, description="JSON string of Notion sorts array"),
    page_size: int = Query(100, description="Number of results to return"),
    api_key: str = Depends(verify_api_key)
):
    """Query a Notion database"""
    notion = get_notion_client()
    
    # Parse JSON strings into Python objects if provided
    filter_obj = json.loads(filter_json) if filter_json else None
    sorts_array = json.loads(sorts_json) if sorts_json else None
    
    # Build the query parameters
    query_params = {
        "database_id": database_id,
        "page_size": page_size
    }
    
    if filter_obj:
        query_params["filter"] = filter_obj
    
    if sorts_array:
        query_params["sorts"] = sorts_array
    
    try:
        result = notion.databases.query(**query_params)
        
        return {
            "success": True,
            "data": {
                "results": result.get("results", []),
                "has_more": result.get("has_more", False),
                "next_cursor": result.get("next_cursor")
            }
        }
    except Exception as e:
        logger.error(f"Notion API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Notion API error: {str(e)}")

# Endpoints - GitHub Integration
@router.post("/integrations/github/issue/create", response_model=Response)
@handle_google_api_error
async def create_github_issue(
    request: GitHubIssueCreateRequest,
    api_key: str = Depends(verify_api_key)
):
    """Create an issue in a GitHub repository"""
    github = get_github_client()
    
    try:
        # Parse owner/repo format
        owner, repo_name = request.repo.split('/')
        repo = github.get_repo(request.repo)
        
        # Create issue
        issue = repo.create_issue(
            title=request.title,
            body=request.body,
            labels=request.labels,
            assignees=request.assignees
        )
        
        return {
            "success": True,
            "data": {
                "issue_id": issue.id,
                "issue_number": issue.number,
                "html_url": issue.html_url
            }
        }
    except Exception as e:
        logger.error(f"GitHub API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")

@router.post("/integrations/github/project/add-card", response_model=Response)
@handle_google_api_error
async def add_issue_to_project(
    request: GitHubProjectCardRequest,
    api_key: str = Depends(verify_api_key)
):
    """Add an issue to a GitHub project"""
    github = get_github_client()
    
    try:
        # Get repo and project
        repo = github.get_repo(request.repo)
        project = repo.get_project(request.project_id)
        issue = repo.get_issue(request.issue_id)
        
        # Create card in first column (backlog/to-do)
        columns = list(project.get_columns())
        if not columns:
            raise HTTPException(status_code=400, detail="Project has no columns")
        
        card = columns[0].create_card(content_id=issue.id, content_type="Issue")
        
        return {
            "success": True,
            "data": {
                "card_id": card.id,
                "card_url": card.url,
                "column_name": columns[0].name
            }
        }
    except Exception as e:
        logger.error(f"GitHub API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GitHub API error: {str(e)}")

@router.get("/integrations/notion/status", response_model=Response)
async def check_notion_status(
    api_key: str = Depends(verify_api_key)
):
    """Check if Notion integration is available and configured"""
    is_available = NOTION_AVAILABLE
    is_configured = bool(os.getenv(NOTION_API_KEY_ENV))
    
    return {
        "success": True,
        "data": {
            "available": is_available,
            "configured": is_configured,
            "status": "ready" if (is_available and is_configured) else "not_ready"
        }
    }

@router.get("/integrations/github/status", response_model=Response)
async def check_github_status(
    api_key: str = Depends(verify_api_key)
):
    """Check if GitHub integration is available and configured"""
    is_available = GITHUB_AVAILABLE
    is_configured = bool(os.getenv(GITHUB_API_KEY_ENV))
    
    return {
        "success": True,
        "data": {
            "available": is_available,
            "configured": is_configured,
            "status": "ready" if (is_available and is_configured) else "not_ready"
        }
    }
