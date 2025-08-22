from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # 应用设置
    app_name: str = "Taskly Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器设置
    host: str = "0.0.0.0"
    port: int = 8000
    
    # 数据库设置
    database_url: str = "mysql+pymysql://root:123456@localhost:3306/test"
    
    # Redis设置
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    
    # JWT设置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS设置
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Celery设置
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # WebSocket设置
    websocket_max_connections: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()