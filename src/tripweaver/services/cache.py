"""LLM 响应缓存 — 基于 Redis，TTL 24小时"""

import hashlib
import json

import structlog

from tripweaver.core.redis import get_redis
from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse

logger = structlog.get_logger(__name__)

CACHE_KEY_PREFIX = "llm_cache"
CACHE_TTL = 86400  # 24小时


def make_cache_key(request: ItineraryRequest) -> str:
    """基于请求参数生成缓存 key。"""
    data = {
        "destination": request.destination,
        "days": request.days,
        "interests": sorted(request.interests),
        "range_mode": request.range_mode,
        "range_minutes": request.range_minutes,
    }
    h = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    return f"{CACHE_KEY_PREFIX}:{h}"


async def get_cached(key: str) -> ItineraryResponse | None:
    """从缓存读取，未命中或错误返回 None。"""
    redis = await get_redis()
    try:
        raw = await redis.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        # itinerary_id 不从缓存读取，命中后由调用方分配
        data["itinerary_id"] = None
        return ItineraryResponse.model_validate(data)
    except Exception as e:
        logger.warning("缓存读取失败", key=key, error=str(e))
        return None


async def set_cached(key: str, response: ItineraryResponse) -> None:
    """写入缓存，仅存储 plan_results 部分。"""
    redis = await get_redis()
    try:
        payload = {
            "destination": response.destination,
            "overview": response.overview,
            "items": [item.model_dump() for item in response.items],
            "plan_options": response.plan_options,
        }
        await redis.setex(key, CACHE_TTL, json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.warning("缓存写入失败", key=key, error=str(e))


async def get_cache_stats() -> dict:
    """返回缓存统计：命中次数、未命中次数、缓存 key 数量。"""
    redis = await get_redis()
    try:
        hits = int(await redis.get(f"{CACHE_KEY_PREFIX}:__stats_hits") or 0)
        misses = int(await redis.get(f"{CACHE_KEY_PREFIX}:__stats_misses") or 0)
        keys = await redis.keys(f"{CACHE_KEY_PREFIX}:*")
        real_keys = [k for k in keys if not k.endswith("__stats_hits") and not k.endswith("__stats_misses")]
        return {"hits": hits, "misses": misses, "keys_count": len(real_keys)}
    except Exception as e:
        logger.warning("缓存统计失败", error=str(e))
        return {"hits": 0, "misses": 0, "keys_count": 0, "error": str(e)}


async def incr_stats(hits: bool) -> None:
    """递增命中/未命中计数。"""
    redis = await get_redis()
    key = f"{CACHE_KEY_PREFIX}:__stats_hits" if hits else f"{CACHE_KEY_PREFIX}:__stats_misses"
    try:
        await redis.incr(key)
    except Exception:
        pass


async def clear_cache() -> int:
    """清空所有 LLM 缓存 key，返回删除数量。"""
    redis = await get_redis()
    try:
        keys = await redis.keys(f"{CACHE_KEY_PREFIX}:*")
        if not keys:
            return 0
        # 排除统计 key
        real_keys = [k for k in keys if not k.endswith("__stats_hits") and not k.endswith("__stats_misses")]
        if real_keys:
            return await redis.delete(*real_keys)
        return 0
    except Exception as e:
        logger.warning("缓存清空失败", error=str(e))
        return 0
