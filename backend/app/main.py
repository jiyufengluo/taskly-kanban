from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.core.redis import redis_client
from app.api.v1.endpoints import auth, projects, lists, cards, users
from app.api.v1.websocket import websocket_manager
import uvicorn

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Taskly Backend API - 高性能任务管理系统",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["项目"])
app.include_router(lists.router, prefix="/api/v1/lists", tags=["列表"])
app.include_router(cards.router, prefix="/api/v1/cards", tags=["卡片"])

# 包含WebSocket路由
app.include_router(websocket_manager.router, prefix="/api/v1/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查Redis连接
        redis_client.ping()
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        ws_ping_interval=20,
        ws_ping_timeout=10
    )