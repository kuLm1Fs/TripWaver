from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from tripweaver.core.config import get_settings
from tripweaver.core.db import get_db
from tripweaver.core.deps import get_current_user_id
from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.models.itinerary import Itinerary
from tripweaver.providers.factory import build_llm_provider, build_search_provider
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
