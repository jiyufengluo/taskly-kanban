from app.core.config import settings

# 应用名称
APP_NAME = settings.app_name
DEBUG = settings.debug

# 数据库配置
DATABASE_URL = settings.database_url

# Redis配置
REDIS_URL = settings.redis_url

# JWT配置
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# CORS配置
CORS_ORIGINS = settings.cors_origins

# Celery配置
CELERY_BROKER_URL = settings.celery_broker_url
CELERY_RESULT_BACKEND = settings.celery_result_backend

# WebSocket配置
WEBSOCKET_MAX_CONNECTIONS = settings.websocket_max_connections