from typing import override

from tavily import AsyncTavilyClient

from tripweaver.core.config import Settings
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.base import SearchProvider, SupplementSearchProvider


class MockSearchProvider(SearchProvider):
    @override
    async def search_places(self, request: ItineraryRequest) -> list[CandidatePlace]:
        destination = request.destination

        return [
            CandidatePlace(
                name=f"{destination} Museum",
                category="museum",
                reason=f"A popular museum in {destination}",
            ),
            CandidatePlace(
                name=f"{destination} Old Town",
                category="landmark",
                reason=f"A classic landmark area in {destination}",
            ),
            CandidatePlace(
                name=f"{destination} Food Street",
                category="food",
                reason=f"A food-focused stop in {destination}",
            ),
        ]


class MockSupplementSearchProvider(SupplementSearchProvider):
    @override
    async def search_guides(self, request: ItineraryRequest) -> str:
        return f"{request.destination}是一个热门旅游目的地，以丰富的美食和文化景点闻名。"


class TavilySupplementSearchProvider(SupplementSearchProvider):
    """使用 Tavily 搜索目的地攻略/评价等补充信息"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    @override
    async def search_guides(self, request: ItineraryRequest) -> str:
        if not self.settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for supplement search")

        interests = ", ".join(request.interests + request.custom_tags) or "旅游"
        query = f"{request.destination} 旅游攻略 {interests} 推荐 必去景点 美食"

        try:
            response = await self.client.search(
                query=query,
                search_depth="basic",
                max_results=5,
                include_answer=True,
                include_raw_content=False,
            )
        except Exception as e:
            raise RuntimeError(f"Tavily search failed: {str(e)}") from e

        # 兼容SDK返回对象或者字典两种情况
        if hasattr(response, "answer"):
            answer = response.answer or ""
        else:
            answer = response.get("answer", "")

        if hasattr(response, "results"):
            results = response.results
        else:
            results = response.get("results", [])

        # 拼接攻略摘要
        parts = []
        if answer:
            parts.append(f"【攻略摘要】{answer}")

        for item in results:
            if hasattr(item, "title"):
                title = item.title
                content = item.content
            else:
                title = item.get("title")
                content = item.get("content")
            if title and content:
                parts.append(f"【{title}】{content[:200]}")

        return "\n".join(parts) if parts else ""
