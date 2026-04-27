import redis.asyncio as redis

from tripweaver.core.config import get_settings

settings = get_settings()

redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def get_redis() -> redis.Redis:
    """依赖注入：获取Redis客户端"""
    return redis_client
