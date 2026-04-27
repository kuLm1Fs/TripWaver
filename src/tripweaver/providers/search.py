from typing import override

from tavily import AsyncTavilyClient
from typing import override
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.base import SearchProvider
from tripweaver.core.config import Settings


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


class TavilySearchProvider(SearchProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    @override
    async def search_places(self, request: ItineraryRequest) -> list[CandidatePlace]:
        if not self.settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required when SEARCH_PROVIDER=tavily")

        query_parts = [request.destination, "top travel attractions places to visit"]
        query_parts.extend(request.interests)
        query = " ".join(query_parts)

        response = await self.client.search(
            query=query,
            search_depth="basic",
            max_results=5,
            include_answer=False,
            include_raw_content=False,
        )

        results = response.get("results", [])

        places: list[CandidatePlace] = []

        for item in results:
            title = item.get("title")
            content = item.get("content")

            if not title:
                continue

            places.append(
                CandidatePlace(
                    name=title,
                    category="attraction",
                    reason=content or "Found via Tavily Search",
                )
            )
        return places
