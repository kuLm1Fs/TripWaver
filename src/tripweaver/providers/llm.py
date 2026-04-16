from typing import override
from tripweaver.domain.schemas import (
    CandidatePlace,
    ItineraryResponse,
    ItineraryItem,
    ItineraryRequest,
)
from tripweaver.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    @override
    async def generate_itinerary(
        self, request: ItineraryRequest, candidates: list[CandidatePlace]
    ) -> ItineraryResponse:
        items = []

        for day in range(1, request.days + 1):
            items.append(
                ItineraryItem(
                    day=day,
                    title=f"Day {day} in {request.destination}",
                    summary="A simple mock itinerary day",
                    places=candidates,
                )
            )
        return ItineraryResponse(
            destination=request.destination,
            overview=f"A {request.days}-day trip in {request.destination}",
            items=items,
        )
