from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, projects, boards, cards, websocket
import json

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A real-time collaborative Kanban board application"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(boards.router, prefix="/api/boards", tags=["boards"])
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(websocket.router, prefix="/api", tags=["websocket"])

@app.get("/")
async def root():
    return {"message": "Welcome to Taskly Kanban Board API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/api")
async def api_info():
    return {
        "message": "Taskly API",
        "version": settings.APP_VERSION,
        "endpoints": {
            "auth": "/api/auth",
            "projects": "/api/projects",
            "boards": "/api/boards",
            "cards": "/api/cards",
            "websocket": "/api/ws/{project_id}"
        }
    }

# WebSocket endpoint is now handled in websocket.router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)