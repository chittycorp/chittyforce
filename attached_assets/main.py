from fastapi import FastAPI
from drive import router as drive_router
from sheets import router as sheets_router
from docs import router as docs_router
from slides import router as slides_router

app = FastAPI()

app.include_router(drive_router)
app.include_router(sheets_router)
app.include_router(docs_router)
app.include_router(slides_router)
