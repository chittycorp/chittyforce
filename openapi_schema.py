from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import json
import os

def generate_openapi_schema(app: FastAPI):
    """
    Generate a custom OpenAPI schema for the application.
    
    Args:
        app: The FastAPI application
        
    Returns:
        A function that generates the OpenAPI schema
    """
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="SecureKey Workspace Agent",
            version="1.0.0",
            description="Autonomous API agent with full access to Google Drive, Docs, Sheets, and Slides",
            routes=app.routes,
        )
        
        # Customize the schema with additional information
        openapi_schema["info"]["x-logo"] = {
            "url": "https://your-logo-url.com/logo.png"
        }
        
        # Add security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "API key"
            }
        }
        
        # Apply security globally
        openapi_schema["security"] = [
            {"bearerAuth": []}
        ]
        
        # Add examples and additional information
        for path in openapi_schema["paths"]:
            for method in openapi_schema["paths"][path]:
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue
                
                # Add description about authentication
                if "description" in openapi_schema["paths"][path][method]:
                    openapi_schema["paths"][path][method]["description"] += "\n\nRequires API key authentication."
                else:
                    openapi_schema["paths"][path][method]["description"] = "Requires API key authentication."
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    return custom_openapi
