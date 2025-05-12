"""
Simple script to run FastAPI with uvicorn
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000)