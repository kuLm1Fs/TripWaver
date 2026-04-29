from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from tripweaver.core.config import get_settings
from tripweaver.core.db import get_db
from tripweaver.core.deps import get_current_user_id
from tripweaver.domain.schemas import (
    ItineraryRequest,
    ItineraryResponse,
    UpdateItineraryRequest,
    UpdateDayPlacesRequest,
    RegenerateDayRequest,
    CustomPlanRequest,
)
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
    request_data: ItineraryRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> ItineraryResponse:
    from tripweaver.core.ratelimit import WINDOW_SECONDS, is_rate_limited

    rate_key = f"ratelimit:plan:{user_id}"
    limited, count = await is_rate_limited(rate_key)
    if limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"请求过于频繁，请{WINDOW_SECONDS // 60}分钟后再试（{count}次）",
        )

    settings = get_settings()
    search_provider = build_search_provider(settings)

    # 如果是高德搜索，同时用于坐标回填
    amap_provider = None
    from tripweaver.providers.amap import AmapSearchProvider
    if isinstance(search_provider, AmapSearchProvider):
        amap_provider = search_provider

    planner = PlannerService(
        search_provider=search_provider,
        llm_provider=build_llm_provider(settings),
        supplement_provider=build_supplement_provider(settings),
        amap_provider=amap_provider,
    )
    # 生成行程
    response = await planner.plan(request_data)
    
    # 存储到数据库
    itinerary = Itinerary(
        creator_id=user_id,
        destination=request_data.destination,
        days=request_data.days,
        interests=request_data.interests,
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


@router.delete("/{itinerary_id}", summary="删除行程")
async def delete_itinerary(
    itinerary_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除行程，仅创建者可操作，同时清理关联数据"""
    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在",
        )
    if itinerary.creator_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以删除行程",
        )

    # 删除关联数据
    from tripweaver.models.itinerary import ItineraryMember
    from tripweaver.models.share import ShareLink
    from tripweaver.models.vote import Vote

    await db.execute(delete(Vote).where(Vote.itinerary_id == itinerary_id))
    await db.execute(delete(ShareLink).where(ShareLink.itinerary_id == itinerary_id))
    await db.execute(delete(ItineraryMember).where(ItineraryMember.itinerary_id == itinerary_id))
    await db.delete(itinerary)
    await db.commit()

    return {"success": True, "message": "行程已删除"}


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


@router.patch("/{itinerary_id}", summary="更新行程概览")
async def update_itinerary(
    itinerary_id: int,
    request: UpdateItineraryRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新行程概览/标题，仅创建者可操作"""
    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")
    if itinerary.creator_id != user_id:
        raise HTTPException(status_code=403, detail="只有创建者可修改")

    plan_results = itinerary.plan_results or {}
    if request.overview is not None:
        plan_results["overview"] = request.overview
    itinerary.plan_results = plan_results
    await db.commit()
    return {"success": True}


@router.put("/{itinerary_id}/days/{day}/places", summary="更新某天地点")
async def update_day_places(
    itinerary_id: int,
    day: int,
    request: UpdateDayPlacesRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """更新某一天的地点列表，仅创建者可操作"""
    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")
    if itinerary.creator_id != user_id:
        raise HTTPException(status_code=403, detail="只有创建者可修改")
    if day < 1 or day > itinerary.days:
        raise HTTPException(status_code=400, detail="天数超出范围")

    plan_results = itinerary.plan_results or {}
    plan_options = plan_results.get("plan_options", [])
    if request.plan_index < 0 or request.plan_index >= len(plan_options):
        raise HTTPException(status_code=400, detail="方案索引无效")

    # 更新指定方案
    plan = plan_options[request.plan_index]
    items = plan.get("items", [])
    day_found = False
    for item in items:
        if item.get("day") == day:
            item["title"] = request.title or item.get("title", "")
            item["summary"] = request.summary or item.get("summary", "")
            item["places"] = [p.model_dump() for p in request.places]
            day_found = True
            break
    if not day_found:
        # 如果没找到对应 day，追加
        items.append({
            "day": day,
            "title": request.title or f"第{day}天",
            "summary": request.summary or "",
            "places": [p.model_dump() for p in request.places],
        })
    plan["items"] = items
    plan_options[request.plan_index] = plan
    plan_results["plan_options"] = plan_options
    itinerary.plan_results = plan_results
    await db.commit()
    return {"success": True}


@router.post("/{itinerary_id}/regenerate-day", summary="重新生成某天行程")
async def regenerate_day(
    itinerary_id: int,
    request: RegenerateDayRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """重新生成某一天的行程，使用与原方案相同的风格"""
    itinerary = await db.get(Itinerary, itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="行程不存在")
    if itinerary.creator_id != user_id:
        raise HTTPException(status_code=403, detail="只有创建者可操作")
    if request.day < 1 or request.day > itinerary.days:
        raise HTTPException(status_code=400, detail="天数超出范围")

    plan_results = itinerary.plan_results or {}
    plan_options = plan_results.get("plan_options", [])
    if request.plan_index < 0 or request.plan_index >= len(plan_options):
        raise HTTPException(status_code=400, detail="方案索引无效")

    # 获取原方案风格
    original_plan = plan_options[request.plan_index]
    style_title = original_plan.get("title", "景点打卡")
    style = next((s for s in [
        {"key": "relaxed_eating", "title": "休闲逛吃", "instruction": "侧重美食探店、轻松休闲，适合吃货朋友。优先安排餐饮、甜品、饮品、小吃等美食类地点，穿插轻松的休闲活动。节奏要慢，每段停留1-2小时，不要赶路。"},
        {"key": "landmark_tour", "title": "景点打卡", "instruction": "涵盖当地经典必去景点，适合第一次来玩的游客。优先安排地标性景点、历史文化场所、网红打卡地。路线要合理，减少重复步行，一天走完核心景点。"},
        {"key": "hidden_gems", "title": "小众特色", "instruction": "挖掘本地人常去的小众好去处，避开人流。优先安排小众公园、本地小店、非热门但有特色的地方。不要安排热门景区和网红店，追求独特体验。"},
    ] if s["title"] == style_title), None)
    if not style:
        style = {"key": "landmark_tour", "title": "景点打卡", "instruction": "涵盖当地经典必去景点，适合第一次来玩的游客。优先安排地标性景点、历史文化场所、网红打卡地。路线要合理，减少重复步行，一天走完核心景点。"}

    # 重新搜索候选地点
    settings = get_settings()
    search_provider = build_search_provider(settings)
    from tripweaver.domain.schemas import ItineraryRequest as ReqSchema
    search_req = ReqSchema(
        destination=itinerary.destination,
        days=itinerary.days,
        interests=request.interests or itinerary.interests or [],
        latitude=itinerary.user_params.get("latitude") if itinerary.user_params else None,
        longitude=itinerary.user_params.get("longitude") if itinerary.user_params else None,
        range_mode=itinerary.user_params.get("range_mode", "walking") if itinerary.user_params else "walking",
        range_minutes=itinerary.user_params.get("range_minutes", 20) if itinerary.user_params else 20,
    )
    candidates = await search_provider.search_places(search_req)

    # 调用 LLM 生成单日行程
    llm_provider = build_llm_provider(settings)
    from tripweaver.providers.llm_prompt import build_single_day_prompt
    prompt = build_single_day_prompt(search_req, candidates, style, request.day)
    text = await llm_provider._call_llm(prompt, label=f"regenerate_day_{request.day}")
    import json
    data = json.loads(text)
    new_items = data if isinstance(data, list) else [data]

    # 更新 plan_results
    plan = plan_options[request.plan_index]
    items = plan.get("items", [])
    # 替换或追加
    items = [item for item in items if item.get("day") != request.day]
    items.extend(new_items)
    items.sort(key=lambda x: x.get("day", 0))
    plan["items"] = items
    plan_options
    plan_options[request.plan_index] = plan
    plan_results["plan_options"] = plan_options
    itinerary.plan_results = plan_results
    await db.commit()
    return {"success": True, "day": request.day, "items": new_items}


@router.get("/candidates", summary="获取候选 POI 列表")
async def get_candidates(
    destination: str,
    days: int = 1,
    interests: str = "",
    range_mode: str = "walking",
    range_minutes: int = 20,
    custom_tags: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
    address: str | None = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """获取候选 POI 列表，供用户选择后生成自定义行程"""
    from tripweaver.domain.schemas import ItineraryRequest as ReqSchema

    request = ReqSchema(
        destination=destination,
        days=days,
        interests=interests.split(",") if interests else [],
        range_mode=range_mode,
        range_minutes=range_minutes,
        custom_tags=custom_tags.split(",") if custom_tags else [],
        latitude=latitude,
        longitude=longitude,
        address=address,
    )

    settings = get_settings()
    search_provider = build_search_provider(settings)
    candidates = await search_provider.search_places(request)

    return {
        "destination": destination,
        "pois": [c.model_dump() for c in candidates],
    }


@router.post("/custom", response_model=ItineraryResponse, summary="自定义行程生成")
async def create_custom_plan(
    request: CustomPlanRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """使用用户选择的 POI 生成自定义行程"""
    from tripweaver.providers.llm_prompt import PLAN_STYLES, build_custom_plan_prompt

    settings = get_settings()
    llm_provider = build_llm_provider(settings)

    # 使用第一个方案的默认风格
    style = PLAN_STYLES[0]

    # 并行生成（目前只有一种风格，直接生成）
    prompt = build_custom_plan_prompt(request, request.selected_pois, style)
    text = await llm_provider._call_llm(prompt, label="custom_plan")

    import json
    data = json.loads(text)
    plan = data if isinstance(data, dict) else data[0]

    items = llm_provider._parse_items(plan.get("items", []))

    response = ItineraryResponse(
        destination=plan.get("destination", request.destination),
        overview=plan.get("overview", ""),
        items=items,
        plan_options=[plan],
    )

    # 存储到数据库
    itinerary = Itinerary(
        creator_id=user_id,
        destination=request.destination,
        days=request.days,
        interests=request.interests,
        user_params={
            "latitude": request.latitude,
            "longitude": request.longitude,
            "range_mode": request.range_mode,
            "range_minutes": request.range_minutes,
        },
        plan_results=response.model_dump(),
    )
    db.add(itinerary)
    await db.commit()
    await db.refresh(itinerary)

    response.itinerary_id = itinerary.id
    return response
