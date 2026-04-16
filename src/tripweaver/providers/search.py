import httpx

from typing import override
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.base import SearchProvider
from tripweaver.core.config import Settings
from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest
from tripweaver.providers.base import SearchProvider


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


class BraveSearchProvider(SearchProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @override
    async def search_places(self, request: ItineraryRequest) -> list[CandidatePlace]:
        if not self.settings.brave_api_key:
            raise ValueError("BRAVE_API_KEY is required when SEARCH_PROVIDER=brave")

        query_parts = [request.destination, "travel attractions"]
        query_parts.extend(request.interests)
        query = " ".join(query_parts)

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.settings.brave_api_key,
        }

        params = {
            "q": query,
            "count": 5,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                self.settings.brave_base_url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()

        data = response.json()
        results = data.get("web", {}).get("results", [])

        places: list[CandidatePlace] = []

        for item in results:
            title = item.get("title")
            description = item.get("description")

            if not title:
                continue

            places.append(
                CandidatePlace(
                    name=title,
                    category="search_result",
                    reason=description or "Found via Brave Search",
                )
            )
        return places
