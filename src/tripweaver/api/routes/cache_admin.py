"""缓存管理接口"""

from fastapi import APIRouter, Depends

from tripweaver.core.deps import get_current_user_id
from tripweaver.services.cache import clear_cache, get_cache_stats

router = APIRouter(prefix="/admin/cache", tags=["管理"])


@router.get("/stats", summary="缓存统计")
async def cache_stats(user_id: int = Depends(get_current_user_id)) -> dict:
    """返回缓存命中率统计和 key 数量。"""
    return await get_cache_stats()


@router.delete("", summary="清空缓存")
async def cache_clear(user_id: int = Depends(get_current_user_id)) -> dict:
    """清空所有 LLM 缓存。"""
    cleared = await clear_cache()
    return {"success": True, "cleared": cleared}
