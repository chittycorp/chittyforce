from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import logging
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

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    templates = Jinja2Templates(directory="templates")
except Exception as e:
    logger.error(f"Failed to mount static files: {e}")

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
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "title": "SecureKey Workspace Agent"}
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

# Define ASGI app
app_asgi = app

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
