"""行程规划服务 — 串联搜索、攻略、LLM 生成"""

import structlog

from tripweaver.domain.schemas import ItineraryRequest, ItineraryResponse
from tripweaver.providers.base import LLMProvider, SearchProvider, SupplementSearchProvider

logger = structlog.get_logger(__name__)


class PlannerService:
    def __init__(
        self,
        search_provider: SearchProvider,
        llm_provider: LLMProvider,
        supplement_provider: SupplementSearchProvider | None = None,
    ) -> None:
        self.search_provider = search_provider
        self.llm_provider = llm_provider
        self.supplement_provider = supplement_provider

    async def plan(self, request: ItineraryRequest) -> ItineraryResponse:
        # 1. 高德搜索周边 POI
        logger.info("开始搜索POI", destination=request.destination, range_mode=request.range_mode)
        candidates = await self.search_provider.search_places(request)
        logger.info("POI搜索完成", count=len(candidates))

        # 2. Tavily 搜索攻略补充信息
        guide_text = ""
        if self.supplement_provider:
            try:
                logger.info("开始搜索攻略")
                guide_text = await self.supplement_provider.search_guides(request)
                logger.info("攻略搜索完成", length=len(guide_text))
            except Exception as e:
                logger.warning("攻略搜索失败，继续流程", error=str(e))

        # 3. LLM 生成多方案行程
        logger.info("开始LLM生成行程")
        itinerary = await self.llm_provider.generate_itinerary(
            request, candidates, guide_text
        )
        logger.info("行程生成完成", plans=len(itinerary.plan_options))

        return itinerary
