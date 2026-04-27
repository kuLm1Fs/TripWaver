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
        # 生成模拟的3个方案
        plan_options = [
            {
                "plan_name": "休闲逛吃",
                "plan_desc": "适合喜欢美食探店、轻松休闲的朋友",
                "destination": request.destination,
                "overview": f"休闲吃逛{request.days}天行程",
                "items": [item.model_dump() for item in items]
            },
            {
                "plan_name": "景点打卡",
                "plan_desc": "涵盖当地经典必去景点，适合第一次来玩的游客",
                "destination": request.destination,
                "overview": f"经典景点{request.days}天打卡行程",
                "items": [item.model_dump() for item in items]
            },
            {
                "plan_name": "小众特色",
                "plan_desc": "挖掘本地人常去的小众好去处，避开人流",
                "destination": request.destination,
                "overview": f"小众特色{request.days}天深度行程",
                "items": [item.model_dump() for item in items]
            }
        ]
        return ItineraryResponse(
            destination=request.destination,
            overview=f"A {request.days}-day trip in {request.destination}",
            items=items,
            plan_options=plan_options
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
        # 适配返回数组或者单个对象的情况
        data = json.loads(text)
        if isinstance(data, list):
            # 多方案返回，取第一个作为默认方案
            plan_options = data
            main_plan = data[0] if data else {}
        else:
            # 兼容单个方案返回
            plan_options = [data]
            main_plan = data
        
        # 解析主方案
        items = []
        for item in main_plan.get("items", []):
            places = []

            for place in item.get("places", []):
                places.append(
                    CandidatePlace(
                        name=place.get("name", "Unknown place"),
                        category=place.get("category", "unknown"),
                        reason=place.get("reason", ""),
                        address=place.get("address", ""),
                        longitude=place.get("longitude"),
                        latitude=place.get("latitude"),
                        price=place.get("price", ""),
                        business_hours=place.get("business_hours", ""),
                        tags=place.get("tags", []),
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
            destination=main_plan.get("destination", request.destination),
            overview=main_plan.get("overview", ""),
            items=items,
            plan_options=plan_options
        )
