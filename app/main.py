from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers.incidents import router as incidents_router
from app.database import engine, Base
import os

# Create tables on start
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Deeps Systems OpsCentre API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(incidents_router)

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    ui_path = "opscentre-ui.html"
    if os.path.exists(ui_path):
        with open(ui_path, "r") as f:
            return f.read()
    return "<h1>OpsCentre UI not found</h1>"

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
