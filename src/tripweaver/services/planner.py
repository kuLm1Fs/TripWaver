# 1. 接收 ItineraryRequest
# 调用搜索 provider，拿到 list[CandidatePlace]
# 调用 LLM provider，生成 ItineraryResponse
# 把结果返回

from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.providers.base import LLMProvider, SearchProvider


class PlannerService:
    def __init__(self, search_provider: SearchProvider, llm_provider: LLMProvider) -> None:
        self.search_provider = search_provider
        self.llm_provider = llm_provider

    async def plan(self, request: ItineraryRequest) -> ItineraryResponse:
        # TODO: 没有具体实现
        candidates = await self.search_provider.search_places(request)  # 没有具体实现
        # TODO:没有具体实现
        itinerary = await self.llm_provider.generate_itinerary(request, candidates)  # 没有具体实现
        return itinerary
