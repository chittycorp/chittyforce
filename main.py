from fastapi import FastAPI, HTTPException, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader
import os
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="SecureKey Workspace Agent",
    description="Autonomous API agent with full access to Google Drive, Docs, Sheets, and Slides",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the connector for Universal Connector integration
try:
    from connector import (
        key_manager, get_api_key, get_google_sa_key_json, 
        get_notion_api_key, get_github_api_key, setup_google_sa_key_file
    )
    logger.info("Universal Connector integration loaded")
    HAS_CONNECTOR = True
except ImportError as e:
    logger.warning(f"Universal Connector integration not available: {e}")
    HAS_CONNECTOR = False

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

# Setup Google Service Account key file if available from connector
if HAS_CONNECTOR:
    sa_key_file = setup_google_sa_key_file()
    if sa_key_file:
        logger.info(f"Google Service Account key file set up at: {sa_key_file}")
    else:
        logger.warning("Google Service Account key not available from connector")

# Import routers - we'll import these conditionally to handle missing dependencies gracefully
try:
    from drive import router as drive_router
    app.include_router(drive_router, tags=["Drive"])
    logger.info("Drive router included")
except ImportError as e:
    logger.warning(f"Drive router not included: {e}")

try:
    from sheets import router as sheets_router
    app.include_router(sheets_router, tags=["Sheets"])
    logger.info("Sheets router included")
except ImportError as e:
    logger.warning(f"Sheets router not included: {e}")

try:
    from docs import router as docs_router
    app.include_router(docs_router, tags=["Docs"])
    logger.info("Docs router included")
except ImportError as e:
    logger.warning(f"Docs router not included: {e}")

try:
    from slides import router as slides_router
    app.include_router(slides_router, tags=["Slides"])
    logger.info("Slides router included")
except ImportError as e:
    logger.warning(f"Slides router not included: {e}")

try:
    from integrations import router as integrations_router
    app.include_router(integrations_router, tags=["Integrations"])
    logger.info("Integrations router included")
except ImportError as e:
    logger.warning(f"Integrations router not included: {e}")

# Import OpenAPI schema generator
try:
    from openapi_schema import generate_openapi_schema
    app.openapi = generate_openapi_schema(app)
    logger.info("Custom OpenAPI schema generator loaded")
except ImportError as e:
    logger.warning(f"Custom OpenAPI schema generator not loaded: {e}")

# Models for API requests and responses
class KeyRequest(BaseModel):
    name: str
    key: str

class KeyResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class KeyListResponse(BaseModel):
    success: bool
    keys: List[str] = []

# API Key security
api_key_header = APIKeyHeader(name="Authorization")

async def verify_admin_key(api_key: str = Depends(api_key_header)):
    """Verify the admin API key for configuration endpoints."""
    expected_key = os.environ.get("ADMIN_API_KEY")
    
    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Admin API key not configured on the server"
        )
    
    if not api_key.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key format. Expected 'Bearer {token}'"
        )
    
    token = api_key.replace("Bearer ", "")
    
    if token != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key"
        )
    
    return token

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

# Root endpoint - Web Interface
@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def root(request: Request):
    try:
        # Check if API keys are configured
        api_key_configured = bool(get_api_key() if HAS_CONNECTOR else os.environ.get("API_KEY"))
        google_sa_configured = bool(get_google_sa_key_json() if HAS_CONNECTOR else os.environ.get("GOOGLE_SA_KEY_FILE"))
        notion_configured = bool(get_notion_api_key() if HAS_CONNECTOR else os.environ.get("NOTION_API_KEY"))
        github_configured = bool(get_github_api_key() if HAS_CONNECTOR else os.environ.get("GITHUB_API_KEY"))
        
        # Determine if we should redirect to config
        if not api_key_configured or not google_sa_configured:
            return RedirectResponse(url="/config")
        
        return templates.TemplateResponse(
            "index.html", 
            {
                "request": request, 
                "title": "SecureKey Workspace Agent",
                "api_key_configured": api_key_configured,
                "google_sa_configured": google_sa_configured,
                "notion_configured": notion_configured,
                "github_configured": github_configured,
                "has_connector": HAS_CONNECTOR
            }
        )
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return HTMLResponse(content=f"""
        <html>
            <head>
                <title>SecureKey Workspace Agent</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container py-5">
                    <h1>SecureKey Workspace Agent</h1>
                    <p>Status: Online</p>
                    <p>Version: 1.0.0</p>
                    <p>Setup in progress. API endpoints available at /docs</p>
                    <a href="/docs" class="btn btn-primary">View API Documentation</a>
                </div>
            </body>
        </html>
        """)

# Configuration page
@app.get("/config", response_class=HTMLResponse, tags=["UI"])
async def config_page(request: Request):
    try:
        return templates.TemplateResponse(
            "config.html", 
            {
                "request": request, 
                "title": "SecureKey Configuration",
                "has_connector": HAS_CONNECTOR,
                "connector_url": os.environ.get("UNIVERSAL_CONNECTOR_URL", "") if HAS_CONNECTOR else ""
            }
        )
    except Exception as e:
        logger.error(f"Error rendering config template: {e}")
        return HTMLResponse(content=f"""
        <html>
            <head>
                <title>SecureKey Configuration</title>
                <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
            </head>
            <body class="bg-dark text-light">
                <div class="container py-5">
                    <h1>SecureKey Configuration</h1>
                    <p>Error loading configuration page: {str(e)}</p>
                    <a href="/" class="btn btn-primary">Back to Dashboard</a>
                </div>
            </body>
        </html>
        """)

# API Root endpoint
@app.get("/api", tags=["Health"])
async def api_root():
    return {
        "name": "SecureKey Workspace Agent",
        "status": "online",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

# API Endpoints for Universal Connector integration
if HAS_CONNECTOR:
    # Get a key status by name
    @app.get("/api/keys/{key_name}/status", response_model=KeyResponse, tags=["Keys"])
    async def get_key_status(key_name: str):
        """Check if a key exists without retrieving its value."""
        # For security, we only check if key exists but don't return value
        if key_name == "API_KEY":
            api_key = get_api_key()
            exists = bool(api_key)
        elif key_name == "GOOGLE_SA_KEY_JSON":
            google_key = get_google_sa_key_json()
            exists = bool(google_key)
        elif key_name == "NOTION_API_KEY":
            notion_key = get_notion_api_key()
            exists = bool(notion_key)
        elif key_name == "GITHUB_API_KEY":
            github_key = get_github_api_key()
            exists = bool(github_key)
        else:
            response = key_manager.get_key(key_name)
            exists = response.success
        
        return {
            "success": True,
            "data": {"name": key_name, "exists": exists}
        }
    
    # List all key names
    @app.get("/api/keys", response_model=KeyListResponse, tags=["Keys"])
    async def list_keys():
        """List all available key names."""
        response = key_manager.list_keys()
        if response.success and response.data:
            return {"success": True, "keys": response.data.get("keys", [])}
        return {"success": True, "keys": []}
    
    # Store a key (admin only)
    @app.post("/api/keys", response_model=KeyResponse, tags=["Keys"])
    async def store_key(
        request: KeyRequest = Body(...),
        api_key: str = Depends(verify_admin_key)
    ):
        """Store a key in the Universal Connector."""
        response = key_manager.store_key(request.name, request.key)
        if response.success:
            return {
                "success": True,
                "message": f"Key {request.name} stored successfully",
                "data": {"name": request.name}
            }
        return {
            "success": False,
            "message": response.error or "Failed to store key"
        }
    
    # Delete a key (admin only)
    @app.delete("/api/keys/{key_name}", response_model=KeyResponse, tags=["Keys"])
    async def delete_key(
        key_name: str,
        api_key: str = Depends(verify_admin_key)
    ):
        """Delete a key from the Universal Connector."""
        response = key_manager.delete_key(key_name)
        if response.success:
            return {
                "success": True,
                "message": f"Key {key_name} deleted successfully",
                "data": {"name": key_name}
            }
        return {
            "success": False,
            "message": response.error or "Failed to delete key"
        }
    
    # Test connection to Universal Connector
    @app.get("/api/connector/test", response_model=KeyResponse, tags=["Keys"])
    async def test_connector():
        """Test the connection to the Universal Connector."""
        if not key_manager.base_url or not key_manager.api_key:
            return {
                "success": False,
                "message": "Universal Connector not configured"
            }
        
        # Try to list keys as a basic connectivity test
        response = key_manager.list_keys()
        if response.success:
            return {
                "success": True,
                "message": "Successfully connected to Universal Connector",
                "data": {"url": key_manager.base_url}
            }
        return {
            "success": False,
            "message": response.error or "Failed to connect to Universal Connector"
        }

# Define ASGI app
app_asgi = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
