from abc import ABC, abstractmethod

from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest, ItineraryResponse


class SearchProvider(ABC):
    @abstractmethod
    async def search_places(self, request: ItineraryRequest) -> list[CandidatePlace]:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    async def generate_itinerary(
        self,
        request: ItineraryRequest,
        candidates: list[CandidatePlace],
    ) -> ItineraryResponse:
        raise NotImplementedError
