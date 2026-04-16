from fastapi import APIRouter

from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.providers.llm import MockLLMProvider
from tripweaver.providers.search import MockSearchProvider
from tripweaver.services.planner import PlannerService

# 接收客户端发来的 HTTP  请求
# 把请求题解析成 ItineraryRequest
# 调用 PlannerService
# 返回 ItineraryResponse

router = APIRouter(prefix="/itineraries", tags=["itineraries"])


@router.post("/plan", response_model=ItineraryResponse)
async def plan_itinerary(request: ItineraryRequest) -> ItineraryResponse:
    planner = PlannerService(
        search_provider=MockSearchProvider(),
        llm_provider=MockLLMProvider(),
    )
    return await planner.plan(request)
