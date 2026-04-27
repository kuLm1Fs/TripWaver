import json
from typing import override

from volcenginesdkarkruntime import Ark

from tripweaver.core.config import Settings
from tripweaver.domain.schemas import (
    CandidatePlace,
    ItineraryItem,
    ItineraryRequest,
    ItineraryResponse,
)
from tripweaver.providers.base import LLMProvider
from tripweaver.providers.llm_prompt import build_itinerary_prompt


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


class ARKLLMProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = Ark(api_key=settings.ark_api_key, base_url=settings.ark_base_url)

    @override
    async def generate_itinerary(
        self, request: ItineraryRequest, candidates: list[CandidatePlace]
    ) -> ItineraryResponse:
        if not self.settings.ark_api_key:
            raise ValueError("OPENAI_API_KEY is reequired when LLM_PROVIDER = ark")

        prompt = build_itinerary_prompt(request, candidates)

        response = self.client.responses.create(
            model=self.settings.ark_model,
            input=prompt,
        )

        text_parts = []

        for item in response.output:
            if getattr(item, "type", None) != "message":
                continue

            for content in item.content:
                if getattr(content, "type", None) == "output_text":
                    text_parts.append(content.text)
        text = "\n".join(text_parts).strip()
        data = json.loads(text)

        items = []
        for item in data.get("items", []):
            places = []

            for place in item.get("places", []):
                places.append(
                    CandidatePlace(
                        name=place.get("name", "Unknown place"),
                        category=place.get("category", "unknown"),
                        reason=place.get("reason", ""),
                    )
                )

            items.append(
                ItineraryItem(
                    day=item.get("day", 1),
                    title=item.get("title", "Untitled"),
                    summary=item.get("summary", ""),
                    places=places,
                )
            )
        return ItineraryResponse(
            destination=data.get("destination", request.destination),
            overview=data.get("overview", ""),
            items=items,
        )
