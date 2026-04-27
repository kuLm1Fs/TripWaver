from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tripweaver.core.config import get_settings
from tripweaver.core.db import get_db
from tripweaver.core.deps import get_current_user_id
from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.models.itinerary import Itinerary
from tripweaver.providers.factory import (
    build_llm_provider,
    build_search_provider,
    build_supplement_provider,
)
from tripweaver.services.planner import PlannerService

router = APIRouter(prefix="/itineraries", tags=["行程规划"])


@router.post("/plan", response_model=ItineraryResponse, summary="生成行程规划")
async def plan_itinerary(
    request: ItineraryRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ItineraryResponse:
    settings = get_settings()
    planner = PlannerService(
        search_provider=build_search_provider(settings),
        llm_provider=build_llm_provider(settings),
        supplement_provider=build_supplement_provider(settings),
    )
    # 生成行程
    response = await planner.plan(request)
    
    # 存储到数据库
    itinerary = Itinerary(
        creator_id=user_id,
        destination=request.destination,
        days=request.days,
        interests=request.interests,
        plan_results=response.model_dump()
    )
    db.add(itinerary)
    await db.commit()
    await db.refresh(itinerary)
    
    # 填充返回的行程ID
    response.itinerary_id = itinerary.id
    return response


@router.get("", summary="获取我的行程列表")
async def list_itineraries(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户创建的所有行程"""
    result = await db.execute(
        select(Itinerary)
        .where(Itinerary.creator_id == user_id)
        .order_by(Itinerary.created_at.desc())
    )
    itineraries = result.scalars().all()
    return [
        {
            "id": it.id,
            "destination": it.destination,
            "days": it.days,
            "interests": it.interests or [],
            "is_locked": it.is_locked,
            "created_at": it.created_at.isoformat() if it.created_at else None,
        }
        for it in itineraries
    ]


@router.get("/{itinerary_id}", summary="获取行程详情")
async def get_itinerary(
    itinerary_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取行程详情，包含多方案和投票信息"""
    from sqlalchemy import func
    from tripweaver.models.itinerary import ItineraryMember
    from tripweaver.models.share import ShareLink
    from tripweaver.models.vote import Vote
    from tripweaver.models.user import User

    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在",
        )

    # 查询成员
    members_result = await db.execute(
        select(ItineraryMember, User.nickname, User.avatar)
        .join(User, ItineraryMember.user_id == User.id)
        .where(ItineraryMember.itinerary_id == itinerary.id)
        .order_by(ItineraryMember.joined_at)
    )
    members = [
        {
            "user_id": m.user_id,
            "nickname": nick,
            "avatar": av,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
        }
        for m, nick, av in members_result.all()
    ]

    # 投票统计
    vote_stats_result = await db.execute(
        select(Vote.plan_index, func.count(Vote.id).label("count"))
        .where(Vote.itinerary_id == itinerary.id)
        .group_by(Vote.plan_index)
    )
    vote_stats = [
        {"plan_index": pi, "count": c} for pi, c in vote_stats_result.all()
    ]

    # 当前用户投票
    user_vote_result = await db.execute(
        select(Vote.plan_index).where(
            Vote.itinerary_id == itinerary.id,
            Vote.user_id == user_id,
        )
    )
    current_user_vote = user_vote_result.scalar_one_or_none()

    plan_results = itinerary.plan_results or {}

    return {
        "itinerary_id": itinerary.id,
        "destination": itinerary.destination,
        "days": itinerary.days,
        "interests": itinerary.interests or [],
        "overview": plan_results.get("overview", ""),
        "items": plan_results.get("items", []),
        "plan_options": plan_results.get("plan_options", []),
        "is_locked": itinerary.is_locked,
        "locked_at": itinerary.locked_at.isoformat() if itinerary.locked_at else None,
        "final_plan_index": itinerary.final_plan_index,
        "creator_id": itinerary.creator_id,
        "is_creator": itinerary.creator_id == user_id,
        "members": members,
        "vote_stats": vote_stats,
        "current_user_vote": current_user_vote,
        "created_at": itinerary.created_at.isoformat() if itinerary.created_at else None,
        "updated_at": itinerary.updated_at.isoformat() if itinerary.updated_at else None,
    }


@router.get("/{itinerary_id}/route", summary="获取行程路线规划")
async def get_itinerary_route(
    itinerary_id: int,
    plan_index: int = 0,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """根据方案中的 POI 列表，调用高德步行路径规划返回路线坐标"""
    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在",
        )

    plan_results = itinerary.plan_results or {}
    plan_options = plan_results.get("plan_options", [])

    # 获取指定方案的 POI 列表
    if plan_options and 0 <= plan_index < len(plan_options):
        plan = plan_options[plan_index]
        items = plan.get("items", [])
    else:
        items = plan_results.get("items", [])

    # 提取有坐标的 POI
    waypoints = []
    place_names = []
    for item in items:
        for place in item.get("places", []):
            lng = place.get("longitude")
            lat = place.get("latitude")
            if lng is not None and lat is not None:
                waypoints.append((lng, lat))
                place_names.append(place.get("name", ""))

    if len(waypoints) < 2:
        return {"segments": [], "total_distance": 0, "total_duration": 0}

    # 调用高德步行路径规划
    settings = get_settings()
    from tripweaver.providers.amap import AmapSearchProvider
    amap = AmapSearchProvider(settings)
    segments = await amap.plan_walking_route(waypoints)

    # 补充地名信息
    for seg in segments:
        seg["from_name"] = place_names[seg["from"]] if seg["from"] < len(place_names) else ""
        seg["to_name"] = place_names[seg["to"]] if seg["to"] < len(place_names) else ""

    total_distance = sum(s.get("distance", 0) for s in segments)
    total_duration = sum(s.get("duration", 0) for s in segments)

    return {
        "segments": segments,
        "total_distance": total_distance,
        "total_duration": total_duration,
    }
