from fastapi import APIRouter

from tripweaver.core.config import get_settings
from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.providers.factory import build_llm_provider, build_search_provider
from tripweaver.services.planner import PlannerService

# 接收客户端发来的 HTTP  请求
# 把请求题解析成 ItineraryRequest
# 调用 PlannerService
# 返回 ItineraryResponse

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("/plan", response_model=ItineraryResponse)
async def plan_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    settings = get_settings()
    planner = PlannerService(
        search_provider=build_search_provider(settings),
        llm_provider=build_llm_provider(settings),
    )
    return await planner.plan(request)
