"""滑动窗口限流 — 基于 Redis，Redis 不可用时 fail-open"""

import time
from functools import wraps
from typing import Callable

import structlog
from fastapi import HTTPException, Request, status

from tripweaver.core.redis import get_redis

logger = structlog.get_logger(__name__)

# 每 10 分钟窗口内最多 5 次
WINDOW_SECONDS = 600
MAX_REQUESTS = 5


def make_rate_key(request: Request, user_id: int | None) -> str:
    """生成限流计数 key：优先用 user_id，否则用 IP。"""
    identity = str(user_id) if user_id else request.client.host
    return f"ratelimit:plan:{identity}"


async def is_rate_limited(key: str) -> tuple[bool, int]:
    """判断是否触发限流。Redis 不可用时 fail-open（允许通过）。

    Returns:
        (is_limited, current_count)
    """
    try:
        redis = await get_redis()
        now = time.time()
        window_start = now - WINDOW_SECONDS

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, WINDOW_SECONDS + 10)
        results = await pipe.execute()

        count = results[1]
        if count >= MAX_REQUESTS:
            logger.warning("rate_limit_triggered", key=key)
        return count >= MAX_REQUESTS, count
    except Exception as e:
        logger.warning("限流检查失败，fail-open", key=key, error=str(e))
        return False, 0


def rate_limit(key_func: Callable[[Request, int | None], str]):
    """限流装饰器，用于 plan 端点。

    用法：
        @router.post("/plan", ...)
        @rate_limit(lambda req, uid: f"ratelimit:plan:{uid or req.client.host}")
        async def plan(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, user_id: int | None = None, **kwargs):
            key = key_func(request, user_id)
            limited, count = await is_rate_limited(key)
            if limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"请求过于频繁，请 {WINDOW_SECONDS // 60} 分钟后再试（{count}/{MAX_REQUESTS}）",
                )
            return await func(request, user_id, **kwargs)
        return wrapper
    return decorator
