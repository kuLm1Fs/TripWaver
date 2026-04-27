from abc import ABC, abstractmethod

from tripweaver.domain.schemas import CandidatePlace, ItineraryRequest, ItineraryResponse


class SearchProvider(ABC):
    @abstractmethod
    async def search_places(self, request: ItineraryRequest) -> list[CandidatePlace]:
        raise NotImplementedError


class SupplementSearchProvider(ABC):
    """攻略/评价等补充信息搜索"""

    @abstractmethod
    async def search_guides(self, request: ItineraryRequest) -> str:
        """搜索目的地攻略信息，返回文本摘要"""
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    async def generate_itinerary(
        self,
        request: ItineraryRequest,
        candidates: list[CandidatePlace],
        guide_text: str = "",
    ) -> ItineraryResponse:
        raise NotImplementedError
