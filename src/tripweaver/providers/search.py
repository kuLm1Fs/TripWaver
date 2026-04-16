from typing import override
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
