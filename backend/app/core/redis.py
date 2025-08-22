import redis
from app.core.config import settings

# 创建Redis连接
redis_client = redis.from_url(
    settings.redis_url,
    db=settings.redis_db,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)


def get_redis():
    """获取Redis连接"""
    return redis_client


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client
        self.default_ttl = 3600  # 1小时
    
    def set(self, key: str, value: any, ttl: int = None) -> bool:
        """设置缓存"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            return self.client.setex(key, ttl, str(value))
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def get(self, key: str) -> any:
        """获取缓存"""
        try:
            value = self.client.get(key)
            return value if value is not None else None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有键"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Redis clear pattern error: {e}")
            return 0


# 创建缓存实例
cache = RedisCache(redis_client)