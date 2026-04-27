from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CreateShareRequest(BaseModel):
    """创建分享链接请求"""
    itinerary_id: int
    expire_days: int | None = 7  # 默认7天有效期，0表示永久


class CreateShareResponse(BaseModel):
    """创建分享链接响应"""
    share_id: str
    share_url: str
    expire_at: datetime | None
    created_at: datetime


class ItineraryDetailResponse(BaseModel):
    """行程详情响应"""
    itinerary_id: int
    destination: str
    days: int
    interests: list[str]
    plan_results: Any
    is_locked: bool
    locked_at: datetime | None
    final_plan_index: int | None
    creator_id: int
    creator_nickname: str
    created_at: datetime
    updated_at: datetime
    members: list[dict] = []
    vote_stats: list[dict] = []
    current_user_vote: int | None = None
    is_creator: bool = False
