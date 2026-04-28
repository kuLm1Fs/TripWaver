"""健康检查 — 简单存活 + 深度就绪"""

from fastapi import status
from fastapi.responses import JSONResponse

from tripweaver.core.redis import get_redis


async def check_redis() -> bool:
    """检查 Redis 连通性。"""
    try:
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception:
        return False


async def check_db() -> bool:
    """检查数据库连通性。"""
    try:
        from tripweaver.core.db import get_db
        async for db in get_db():
            await db.execute(__import__("sqlalchemy").text("SELECT 1"))
            break
        return True
    except Exception:
        return False


async def health_live() -> dict:
    """简单存活检查 — 应用进程在跑即可。"""
    return {"status": "ok"}


async def health_ready() -> tuple[JSONResponse | None, dict]:
    """深度就绪检查 — 检查 Redis 和 DB 连通性。

    Returns:
        (error_response, body) — error_response 非空表示检查失败
    """
    redis_ok = await check_redis()
    db_ok = await check_db()

    body = {"status": "ok" if (redis_ok and db_ok) else "degraded", "redis": "ok" if redis_ok else "error", "db": "ok" if db_ok else "error"}

    if not (redis_ok and db_ok):
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body), body

    return None, body
