"""滑动窗口限流 — 基于 Redis"""

import time
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request, status

from tripweaver.core.redis import get_redis

# 每 10 分钟窗口内最多 5 次
WINDOW_SECONDS = 600
MAX_REQUESTS = 5


def make_rate_key(request: Request, user_id: int | None) -> str:
    """生成限流计数 key：优先用 user_id，否则用 IP。"""
    identity = str(user_id) if user_id else request.client.host
    return f"ratelimit:plan:{identity}"


async def is_rate_limited(key: str) -> tuple[bool, int]:
    """判断是否触发限流。

    Returns:
        (is_limited, current_count)
    """
    redis = await get_redis()
    now = time.time()
    window_start = now - WINDOW_SECONDS

    pipe = redis.pipeline()
    # 删除窗口外的旧记录
    pipe.zremrangebyscore(key, 0, window_start)
    # 计数当前窗口内请求
    pipe.zcard(key)
    # 加入当前请求
    pipe.zadd(key, {str(now): now})
    # 设置过期
    pipe.expire(key, WINDOW_SECONDS + 10)
    results = await pipe.execute()

    count = results[1]  # zcard 结果
    return count >= MAX_REQUESTS, count


async def increment_rate(key: str) -> None:
    """确认限流通过后正式计数（zadd 已在 is_rate_limited 中写入）。"""
    pass  # 已在 is_rate_limited 中通过 pipeline 写入，无需额外操作


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
